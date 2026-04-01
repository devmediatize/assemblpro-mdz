import httpx
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.configuracao import Configuracao


class SmsService:
    """Serviço para envio de SMS através de diversos provedores"""

    @staticmethod
    async def get_config(db: AsyncSession, chave: str) -> Optional[str]:
        """Obtém uma configuração do banco"""
        result = await db.execute(
            select(Configuracao).where(Configuracao.chave == chave)
        )
        config = result.scalar_one_or_none()
        return config.valor if config else None

    @staticmethod
    async def is_enabled(db: AsyncSession) -> bool:
        """Verifica se o SMS está habilitado"""
        enabled = await SmsService.get_config(db, "smsEnabled")
        return enabled == "true"

    @staticmethod
    async def enviar_sms(
        db: AsyncSession,
        telefone: str,
        mensagem: str
    ) -> dict:
        """
        Envia SMS usando o provedor configurado.
        Retorna dict com 'sucesso' e 'mensagem' ou 'erro'
        """
        if not await SmsService.is_enabled(db):
            # Se SMS não está habilitado, simula envio (modo desenvolvimento)
            print(f"[SMS SIMULADO] Para: {telefone} | Mensagem: {mensagem}")
            return {
                "sucesso": True,
                "mensagem": "SMS simulado (modo desenvolvimento)",
                "simulado": True
            }

        provider = await SmsService.get_config(db, "smsProvider")
        account_id = await SmsService.get_config(db, "smsAccountId")
        auth_token = await SmsService.get_config(db, "smsAuthToken")
        from_number = await SmsService.get_config(db, "smsFromNumber")

        if not all([provider, account_id, auth_token, from_number]):
            return {
                "sucesso": False,
                "erro": "Configurações de SMS incompletas"
            }

        # Formata telefone (remove caracteres especiais)
        telefone_limpo = "".join(filter(str.isdigit, telefone))
        if not telefone_limpo.startswith("55"):
            telefone_limpo = f"55{telefone_limpo}"
        telefone_formatado = f"+{telefone_limpo}"

        try:
            if provider == "comtele":
                return await SmsService._enviar_comtele(
                    auth_token, telefone_formatado, mensagem
                )
            elif provider == "twilio":
                return await SmsService._enviar_twilio(
                    account_id, auth_token, from_number, telefone_formatado, mensagem
                )
            elif provider == "zenvia":
                return await SmsService._enviar_zenvia(
                    account_id, auth_token, telefone_formatado, mensagem
                )
            elif provider == "aws_sns":
                return await SmsService._enviar_aws_sns(
                    account_id, auth_token, telefone_formatado, mensagem
                )
            elif provider == "totalvoice":
                return await SmsService._enviar_totalvoice(
                    auth_token, telefone_formatado, mensagem
                )
            elif provider == "infobip":
                return await SmsService._enviar_infobip(
                    account_id, auth_token, from_number, telefone_formatado, mensagem
                )
            else:
                return {
                    "sucesso": False,
                    "erro": f"Provedor não suportado: {provider}"
                }
        except Exception as e:
            return {
                "sucesso": False,
                "erro": str(e)
            }

    @staticmethod
    async def _enviar_comtele(
        api_key: str,
        to_number: str,
        mensagem: str
    ) -> dict:
        """Envia SMS via Comtele"""
        url = "https://sms.comtele.com.br/api/v2/send"

        # Remove o + do número e código do país (55) se presente
        # Comtele espera formato: DDD + Número (ex: 11999998888)
        numero_limpo = to_number.replace("+", "")
        if numero_limpo.startswith("55"):
            numero_limpo = numero_limpo[2:]  # Remove código do país

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers={
                    "content-type": "application/json",
                    "auth-key": api_key
                },
                json={
                    "Sender": "AssemblPro",
                    "Receivers": numero_limpo,
                    "Content": mensagem
                }
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("Success"):
                    return {
                        "sucesso": True,
                        "mensagem": "SMS enviado com sucesso",
                        "id": data.get("Object", {}).get("requestUniqueId")
                    }
                else:
                    return {
                        "sucesso": False,
                        "erro": data.get("Message", "Erro desconhecido")
                    }
            else:
                return {
                    "sucesso": False,
                    "erro": f"Erro Comtele: {response.text}"
                }

    @staticmethod
    async def _enviar_twilio(
        account_sid: str,
        auth_token: str,
        from_number: str,
        to_number: str,
        mensagem: str
    ) -> dict:
        """Envia SMS via Twilio"""
        url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                auth=(account_sid, auth_token),
                data={
                    "From": from_number,
                    "To": to_number,
                    "Body": mensagem
                }
            )

            if response.status_code in [200, 201]:
                data = response.json()
                return {
                    "sucesso": True,
                    "mensagem": "SMS enviado com sucesso",
                    "sid": data.get("sid")
                }
            else:
                return {
                    "sucesso": False,
                    "erro": f"Erro Twilio: {response.text}"
                }

    @staticmethod
    async def _enviar_zenvia(
        account_id: str,
        auth_token: str,
        to_number: str,
        mensagem: str
    ) -> dict:
        """Envia SMS via Zenvia"""
        url = "https://api.zenvia.com/v2/channels/sms/messages"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers={
                    "X-API-TOKEN": auth_token,
                    "Content-Type": "application/json"
                },
                json={
                    "from": account_id,
                    "to": to_number.replace("+", ""),
                    "contents": [
                        {"type": "text", "text": mensagem}
                    ]
                }
            )

            if response.status_code in [200, 201, 202]:
                return {
                    "sucesso": True,
                    "mensagem": "SMS enviado com sucesso"
                }
            else:
                return {
                    "sucesso": False,
                    "erro": f"Erro Zenvia: {response.text}"
                }

    @staticmethod
    async def _enviar_aws_sns(
        access_key: str,
        secret_key: str,
        to_number: str,
        mensagem: str
    ) -> dict:
        """Envia SMS via AWS SNS"""
        try:
            import boto3
            client = boto3.client(
                "sns",
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name="us-east-1"
            )

            response = client.publish(
                PhoneNumber=to_number,
                Message=mensagem
            )

            return {
                "sucesso": True,
                "mensagem": "SMS enviado com sucesso",
                "message_id": response.get("MessageId")
            }
        except ImportError:
            return {
                "sucesso": False,
                "erro": "Biblioteca boto3 não instalada"
            }
        except Exception as e:
            return {
                "sucesso": False,
                "erro": str(e)
            }

    @staticmethod
    async def _enviar_totalvoice(
        auth_token: str,
        to_number: str,
        mensagem: str
    ) -> dict:
        """Envia SMS via TotalVoice"""
        url = "https://api2.totalvoice.com.br/sms"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers={
                    "Access-Token": auth_token,
                    "Content-Type": "application/json"
                },
                json={
                    "numero_destino": to_number.replace("+", ""),
                    "mensagem": mensagem
                }
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("sucesso"):
                    return {
                        "sucesso": True,
                        "mensagem": "SMS enviado com sucesso"
                    }
                else:
                    return {
                        "sucesso": False,
                        "erro": data.get("motivo", "Erro desconhecido")
                    }
            else:
                return {
                    "sucesso": False,
                    "erro": f"Erro TotalVoice: {response.text}"
                }

    @staticmethod
    async def _enviar_infobip(
        api_key: str,
        base_url: str,
        from_number: str,
        to_number: str,
        mensagem: str
    ) -> dict:
        """Envia SMS via Infobip"""
        url = f"{base_url}/sms/2/text/advanced"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers={
                    "Authorization": f"App {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "messages": [
                        {
                            "from": from_number,
                            "destinations": [{"to": to_number.replace("+", "")}],
                            "text": mensagem
                        }
                    ]
                }
            )

            if response.status_code in [200, 201]:
                return {
                    "sucesso": True,
                    "mensagem": "SMS enviado com sucesso"
                }
            else:
                return {
                    "sucesso": False,
                    "erro": f"Erro Infobip: {response.text}"
                }

    @staticmethod
    async def enviar_codigo_verificacao(
        db: AsyncSession,
        telefone: str,
        codigo: str,
        eleicao_titulo: str
    ) -> dict:
        """Envia código de verificação para votação"""
        mensagem = f"AssemblPro - Seu código de verificação para votar em '{eleicao_titulo}' é: {codigo}. Válido por 5 minutos."
        return await SmsService.enviar_sms(db, telefone, mensagem)
