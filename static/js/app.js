// AssemblPro - JavaScript Principal

// ============ CONFIGURAÇÃO DA API ============
const API_URL = '/api';

// ============ UTILITÁRIOS ============
const utils = {
    // Requisições HTTP
    async fetch(endpoint, options = {}) {
        const token = localStorage.getItem('token');
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };

        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        const response = await fetch(`${API_URL}${endpoint}`, {
            ...options,
            headers
        });

        if (response.status === 401) {
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            window.location.href = '/login';
            return;
        }

        return response;
    },

    // Formatar CPF
    formatCPF(cpf) {
        cpf = cpf.replace(/\D/g, '');
        if (cpf.length <= 3) return cpf;
        if (cpf.length <= 6) return cpf.replace(/(\d{3})(\d{1,3})/, '$1.$2');
        if (cpf.length <= 9) return cpf.replace(/(\d{3})(\d{3})(\d{1,3})/, '$1.$2.$3');
        return cpf.replace(/(\d{3})(\d{3})(\d{3})(\d{1,2})/, '$1.$2.$3-$4');
    },

    // Formatar Telefone
    formatTelefone(tel) {
        tel = tel.replace(/\D/g, '');
        if (tel.length <= 2) return tel;
        if (tel.length <= 6) return tel.replace(/(\d{2})(\d{1,4})/, '($1) $2');
        if (tel.length <= 10) return tel.replace(/(\d{2})(\d{4})(\d{1,4})/, '($1) $2-$3');
        return tel.replace(/(\d{2})(\d{5})(\d{4})/, '($1) $2-$3');
    },

    // Formatar CNPJ
    formatCNPJ(cnpj) {
        cnpj = cnpj.replace(/\D/g, '');
        if (cnpj.length <= 2) return cnpj;
        if (cnpj.length <= 5) return cnpj.replace(/(\d{2})(\d{1,3})/, '$1.$2');
        if (cnpj.length <= 8) return cnpj.replace(/(\d{2})(\d{3})(\d{1,3})/, '$1.$2.$3');
        if (cnpj.length <= 12) return cnpj.replace(/(\d{2})(\d{3})(\d{3})(\d{1,4})/, '$1.$2.$3/$4');
        return cnpj.replace(/(\d{2})(\d{3})(\d{3})(\d{4})(\d{1,2})/, '$1.$2.$3/$4-$5');
    },

    // Formatar CEP
    formatCEP(cep) {
        cep = cep.replace(/\D/g, '');
        if (cep.length <= 5) return cep;
        return cep.replace(/(\d{5})(\d{1,3})/, '$1-$2');
    },

    // Formatar Data (DD/MM/AAAA)
    formatDataInput(data) {
        data = data.replace(/\D/g, '');
        if (data.length <= 2) return data;
        if (data.length <= 4) return data.replace(/(\d{2})(\d{1,2})/, '$1/$2');
        return data.replace(/(\d{2})(\d{2})(\d{1,4})/, '$1/$2/$3');
    },

    // Formatar data para exibição
    formatDate(date) {
        return new Date(date).toLocaleDateString('pt-BR', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    },

    // Toast de notificação
    toast(message, type = 'success') {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'}"></i>
            <span>${message}</span>
        `;
        document.body.appendChild(toast);

        setTimeout(() => {
            toast.classList.add('show');
        }, 100);

        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    },

    // Obter parâmetros da URL
    getUrlParams() {
        const params = new URLSearchParams(window.location.search);
        const result = {};
        for (const [key, value] of params) {
            result[key] = value;
        }
        return result;
    }
};

// ============ AUTENTICAÇÃO ============
const auth = {
    async login(cpf, senha) {
        const response = await utils.fetch('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ cpf, senha })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Erro ao fazer login');
        }

        if (data.requires_otp) {
            localStorage.setItem('temp_token', data.access_token);
            return { requires_otp: true };
        }

        localStorage.setItem('token', data.access_token);
        localStorage.setItem('user', JSON.stringify({
            id: data.user_id,
            nome: data.nome,
            type: data.user_type
        }));

        return data;
    },

    async loginAdmin(email, senha) {
        const response = await utils.fetch('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ email, senha })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Erro ao fazer login');
        }

        localStorage.setItem('token', data.access_token);
        localStorage.setItem('user', JSON.stringify({
            id: data.user_id,
            nome: data.nome,
            type: data.user_type
        }));

        return data;
    },

    async verificarOTP(codigo) {
        const tempToken = localStorage.getItem('temp_token');
        const response = await utils.fetch('/auth/verificar-otp', {
            method: 'POST',
            body: JSON.stringify({ codigo, temp_token: tempToken })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Código inválido');
        }

        localStorage.removeItem('temp_token');
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('user', JSON.stringify({
            id: data.user_id,
            nome: data.nome,
            type: data.user_type
        }));

        return data;
    },

    logout() {
        const user = this.getUser();
        const isAdmin = user && user.type === 'admin';
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = isAdmin ? '/admin/login' : '/login';
    },

    getUser() {
        const user = localStorage.getItem('user');
        return user ? JSON.parse(user) : null;
    },

    isAuthenticated() {
        return !!localStorage.getItem('token');
    }
};

// ============ TEMA ============
const theme = {
    init() {
        const savedTheme = localStorage.getItem('theme') || 'dark';
        this.set(savedTheme);
    },

    set(themeName) {
        document.documentElement.setAttribute('data-theme', themeName);
        localStorage.setItem('theme', themeName);
        this.updateIcon();
        this.updateLogo();
    },

    toggle() {
        const current = localStorage.getItem('theme') || 'dark';
        const newTheme = current === 'dark' ? 'light' : 'dark';
        this.set(newTheme);
    },

    updateIcon() {
        const icon = document.getElementById('themeIcon');
        if (icon) {
            const current = localStorage.getItem('theme') || 'dark';
            icon.className = current === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
        }
    },

    updateLogo() {
        const current = localStorage.getItem('theme') || 'dark';
        const logoSrc = current === 'dark' ? '/static/img/logo.png' : '/static/img/logo2.png';
        const logoBottomSrc = current === 'dark' ? '/static/img/logoassemblpro.png' : '/static/img/logoassemblpro2.png';
        const cacheBust = '?v=' + Date.now();

        // Atualiza logo do sidebar (topo)
        const sidebarLogo = document.getElementById('sidebarLogo');
        if (sidebarLogo) {
            sidebarLogo.src = logoSrc + cacheBust;
        }

        // Atualiza logo do sidebar (rodapé) - usa logoassemblpro
        const sidebarLogoBottom = document.getElementById('sidebarLogoBottom');
        if (sidebarLogoBottom) {
            sidebarLogoBottom.src = logoBottomSrc + cacheBust;
        }

        // Atualiza logos nas páginas de login (topo)
        const loginLogos = document.querySelectorAll('.login-logo .logo-img');
        loginLogos.forEach(logo => {
            logo.src = logoSrc + cacheBust;
        });

        // Atualiza logo do rodapé do login
        const loginLogoBottom = document.getElementById('loginLogoBottom');
        if (loginLogoBottom) {
            loginLogoBottom.src = logoBottomSrc + cacheBust;
        }
    }
};

// ============ ELEIÇÕES ============
const eleicoes = {
    async listar(status = null) {
        let endpoint = '/eleicoes';
        if (status) {
            endpoint += `?status_filter=${status}`;
        }
        const response = await utils.fetch(endpoint);
        return response.json();
    },

    async obter(id) {
        const response = await utils.fetch(`/eleicoes/${id}`);
        return response.json();
    },

    async criar(data) {
        const response = await utils.fetch('/eleicoes', {
            method: 'POST',
            body: JSON.stringify(data)
        });
        return response.json();
    },

    async atualizar(id, data) {
        const response = await utils.fetch(`/eleicoes/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
        return response.json();
    },

    async resultado(id) {
        const response = await utils.fetch(`/eleicoes/${id}/resultado`);
        return response.json();
    }
};

// ============ VOTOS ============
const votos = {
    async registrar(data) {
        const user = auth.getUser();
        const response = await utils.fetch(`/votos?cooperado_id=${user.id}`, {
            method: 'POST',
            body: JSON.stringify(data)
        });
        return response.json();
    },

    async verificarComprovante(hash) {
        const response = await utils.fetch(`/votos/comprovante/${hash}`);
        return response.json();
    }
};

// ============ DASHBOARD ============
const dashboard = {
    async estatisticas() {
        const response = await utils.fetch('/dashboard/estatisticas');
        return response.json();
    },

    async tempoReal(eleicaoId) {
        const response = await utils.fetch(`/dashboard/eleicao/${eleicaoId}/tempo-real`);
        return response.json();
    },

    async participacaoRegiao(eleicaoId) {
        const response = await utils.fetch(`/dashboard/eleicao/${eleicaoId}/participacao-regiao`);
        return response.json();
    }
};

// ============ INICIALIZAÇÃO ============
document.addEventListener('DOMContentLoaded', () => {
    // Inicializa tema
    theme.init();

    // Toggle de tema
    const themeToggle = document.getElementById('themeToggleBtn');
    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            theme.toggle();
        });
    }

    // Máscara de CPF
    const cpfInputs = document.querySelectorAll('input[data-mask="cpf"]');
    cpfInputs.forEach(input => {
        input.addEventListener('input', (e) => {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length > 11) value = value.slice(0, 11);
            e.target.value = utils.formatCPF(value);
        });
    });

    // Máscara de Telefone
    const telInputs = document.querySelectorAll('input[data-mask="telefone"]');
    telInputs.forEach(input => {
        input.addEventListener('input', (e) => {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length > 11) value = value.slice(0, 11);
            e.target.value = utils.formatTelefone(value);
        });
    });

    // Máscara de CNPJ
    const cnpjInputs = document.querySelectorAll('input[data-mask="cnpj"]');
    cnpjInputs.forEach(input => {
        input.addEventListener('input', (e) => {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length > 14) value = value.slice(0, 14);
            e.target.value = utils.formatCNPJ(value);
        });
    });

    // Máscara de CEP
    const cepInputs = document.querySelectorAll('input[data-mask="cep"]');
    cepInputs.forEach(input => {
        input.addEventListener('input', (e) => {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length > 8) value = value.slice(0, 8);
            e.target.value = utils.formatCEP(value);
        });
    });

    // Máscara de Data (DD/MM/AAAA)
    const dataInputs = document.querySelectorAll('input[data-mask="data"]');
    dataInputs.forEach(input => {
        input.addEventListener('input', (e) => {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length > 8) value = value.slice(0, 8);
            e.target.value = utils.formatDataInput(value);
        });
    });

    // Verificar autenticação em páginas protegidas
    const isProtectedPage = !window.location.pathname.includes('/login') &&
                           !window.location.pathname.includes('/verificar-otp');
    const isAdminPage = window.location.pathname.startsWith('/admin');

    if (isProtectedPage && !auth.isAuthenticated()) {
        window.location.href = isAdminPage ? '/admin/login' : '/login';
    }

    // Atualizar nome do usuário
    const userNameEl = document.querySelector('.user-name');
    if (userNameEl) {
        const user = auth.getUser();
        if (user) {
            userNameEl.textContent = user.nome;
        }
    }
});

// Exportar para uso global
window.AssemblPro = {
    utils,
    auth,
    theme,
    eleicoes,
    votos,
    dashboard
};
