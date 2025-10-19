# 🖥️ VirtualGamePad - Servidor PC

Este é o servidor (backend) do projeto **VirtualGamePad**.

Ele é responsável por receber os comandos do [**aplicativo VirtualGamePad Mobile**](https://github.com/Maycon-Fidelis/GamePad_mobile) via WebSocket e traduzi-los em entradas de controle virtual (XInput). Isso permite que seu celular funcione como um controle de Xbox 360 no seu PC.

**Fluxo do Projeto:**
`Celular (App Mobile)` → `Rede Wi-Fi` → `PC (Este Servidor)` → `Jogo (via XInput)`

---

## 📸 Demonstração
<img src="https://github.com/user-attachments/assets/5e7e26a1-649e-4efa-95df-fd213695aee5" alt="Demonstração do VirtualGamePad">

---

## 🚀 Funcionalidades

- 📡 **Recebe comandos** do cliente mobile via WebSocket.
- 🔄 **Traduz gestos** e toques em entradas de controle (eixos, botões).
- 🎮 **Simula um controle** de Xbox 360 (XInput), compatível com a maioria dos jogos de PC.
- ⚡ **Conexão de baixa latência** para uma experiência de jogo fluida.
- 🌐 **Inicia um servidor local** na porta `8083`.

---

## 🛠️ Tecnologias Utilizadas

- **Python 3.x**
- **asyncio:** Para gerenciamento de conexões assíncronas.
- **websockets:** Para a comunicação em tempo real.
- **vgamepad:** Biblioteca para emular o controle XInput.

---

## ⚠️ Pré-requisitos (Importante!)

Não importa qual método de instalação você escolha, você **precisa** de:

1.  **Driver ViGEm Bus (Apenas Windows):** O projeto **exige** o driver "Virtual Gamepad Emulation Framework".
    * Faça o download e instale o `ViGEmBusSetup` mais recente [**aqui**](https://github.com/ViGEm/ViGEmBus/releases).
2.  O aplicativo [**VirtualGamePad Mobile**](https://github.com/Maycon-Fidelis/GamePad_mobile) no seu celular.
3.  PC e Celular conectados na **mesma rede Wi-Fi**.

---

## 📦 Instalação Rápida (Recomendado para Usuários)

Este método é para quem quer apenas **usar** o servidor, sem precisar compilar o projeto.

1.  Vá para a [**página de Releases**](https://github.com/Maycon-Fidelis/GamePad_received/releases/tag/Tag-1) deste repositório.
2.  Baixe o arquivo `.zip` da versão mais recente (ex: `VirtualGamePad-Server-v1.0.zip`).
3.  Extraia o conteúdo do arquivo `.zip` em uma pasta permanente no seu PC.
4.  Execute o `gamePad_received.exe`.
5.  Se o Firewall do Windows perguntar, **permita o acesso** à rede para que o celular possa se conectar.
6.  Pronto! Siga para a seção "Como Usar".

---

## 👨‍💻 Instalação (Para Desenvolvedores)

Este método é para quem quer executar o código-fonte diretamente com Python.

1.  **Clone o repositório:**
    ```bash
    git clone https://github.com/Maycon-Fidelis/GamePad_received
    cd GamePad_received
    ```

2.  **Crie e ative um ambiente virtual (etapa opciona):**
    ```bash
    # Criar o ambiente
    python -m venv venv
    
    # Ativar no Windows
    .\venv\Scripts\activate
    
    # Ativar no Linux/Mac
    source venv/bin/activate
    ```

3.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```
---

## ▶️ Como Usar

1.  **Inicie o servidor:**
    * **Método Rápido:** Dê um duplo clique no `gamePad_received.exe`.
    * **Método Desenvolvedor:** No seu terminal (com o `venv` ativado), execute:
        ```bash
        python main.py
        ```
2.  **Conecte o App Mobile:**
    * Abra o aplicativo **VirtualGamePad Mobile** no seu celular.
    * A interface do servidor no seu PC mostrará as informações de conexão (**IP**, **Porta** e **QR Code**).
    * No app, **escaneie o QR Code** ou **digite o IP e a Porta** manualmente para se conectar.

3.  **Jogue!**
    A iterface do servidor mostrará quando um cliente se conectar, e o celular passará a controlar o PC.

---

## 📜 Licença

Este projeto está sob a licença MIT. Consulte o arquivo `LICENSE` para mais detalhes.

---

## 💡 Desenvolvido por

**Maycon Fidelis**

[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/maycon-fidelis-66a757228/)
[![GitHub](https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/Maycon-Fidelis)