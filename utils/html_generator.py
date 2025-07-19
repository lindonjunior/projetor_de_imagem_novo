# utils/html_generator.py

import json # Importa a biblioteca JSON para um escaping de caracteres mais seguro

def generate_html_with_dynamic_font(text: str) -> str:
    """
    Cria uma página HTML que centraliza o texto e ajusta o tamanho da fonte
    para preencher a tela o máximo possível usando JavaScript.
    Esta versão usa json.dumps para um escaping de caracteres mais robusto e
    um algoritmo de busca de fonte mais eficiente.
    """
    # Usar json.dumps é a maneira mais segura de passar uma string Python para JavaScript.
    # Ele lida com aspas, barras invertidas, novas linhas e outros caracteres especiais.
    js_safe_text = json.dumps(text)

    return f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
    <meta charset="UTF-8">
    <title>Anotações</title>
    <style>
        /* Estilos básicos para preencher a tela e remover margens */
        body, html {{
            margin: 0;
            padding: 0;
            width: 100%;
            height: 100%;
            overflow: hidden; /* Evita barras de rolagem */
            background-color: black;
            color: white;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }}
        /* Container principal que centraliza o conteúdo */
        #container {{
            width: 95vw; /* Usa 95% da largura da viewport */
            height: 95vh; /* Usa 95% da altura da viewport */
            display: flex;
            justify-content: center; /* Centraliza horizontalmente */
            align-items: center;   /* Centraliza verticalmente */
            text-align: center;
            /* A quebra de palavra ajuda a evitar que palavras muito longas estourem o container */
            word-break: break-word;
        }}
    </style>
    </head>
    <body>

    <div id="container"></div>

    <script>
        // Função auto-executável para não poluir o escopo global
        (function() {{
            const container = document.getElementById('container');
            
            // Decodifica o texto que foi passado do Python de forma segura
            const textContent = {js_safe_text};
            
            // Substitui os caracteres de nova linha por tags <br> para quebras de linha em HTML
            container.innerHTML = textContent.replace(/\\n/g, '<br>');

            function fitText() {{
                // Algoritmo de busca binária para encontrar o tamanho ideal da fonte de forma eficiente
                let minFontSize = 10;
                let maxFontSize = 400; // Um limite superior razoável
                let optimalFontSize = minFontSize;

                while (minFontSize <= maxFontSize) {{
                    let currentSize = Math.floor((minFontSize + maxFontSize) / 2);
                    container.style.fontSize = currentSize + 'px';

                    // Verifica se o conteúdo estourou os limites do container
                    if (container.scrollWidth > container.clientWidth || container.scrollHeight > container.clientHeight) {{
                        maxFontSize = currentSize - 1; // Tenta um tamanho menor
                    }} else {{
                        optimalFontSize = currentSize; // Este tamanho coube, vamos tentar um maior
                        minFontSize = currentSize + 1;
                    }}
                }}
                // Aplica o maior tamanho de fonte que coube
                container.style.fontSize = optimalFontSize + 'px';
            }}

            // Roda a função quando a página carregar e se for redimensionada
            window.onload = fitText;
            window.onresize = fitText;
        }})();
    </script>
    </body>
    </html>
    """

