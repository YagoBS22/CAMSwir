# Sistema de Detecção de Umidade SWIR 🪵📷

Este projeto utiliza visão computacional em Python e imagens no espectro infravermelho de ondas curtas (SWIR) para detectar de forma não-destrutiva o teor de umidade em amostras de madeira. Ele se integra nativamente com a câmera **Atlas SWIR 1.3MP (Sony IMX990)** através do Arena SDK.

## Requerimentos

Antes de executar o projeto, certifique-se de possuir os seguintes requisitos instalados e configurados:

1. **Instale as dependências padrão:**
   No terminal da sua pasta, execute:
   ```bash
   pip install -r requirements.txt
2. **Baixe o Arena Python Package do site oficial da Lucid Vision Labs através do link abaixo:**
   [Lucid Vision Labs - Download Hub](https://thinklucid.com/downloads-hub/)

3. **Após o download, extraia o arquivo `.zip` obtido no site da Lucid Vision Labs.
Dentro dele, localize o arquivo `.whl`, por exemplo:**

4. **Instale o Arena SDK (Lucid Vision Labs):**
   No terminal da sua pasta, execute:
   ```bash
   pip install arena_api-2.8.4-py3-none-any.whl
## Como Usar

O projeto possui duas pastas que o próprio código criará automaticamente caso não existam:

### `referencia/`

Coloque aqui as imagens da madeira com níveis de umidade já conhecidos.

*Essa pasta é usada para calibração e comparação matemática.*

### `fotos_comparar/`

As imagens tiradas na bancada serão salvas aqui automaticamente.

*Também é possível colocar imagens manualmente nessa pasta para análise offline.*

## Execução

Execute o arquivo principal:

```bash
python main.py
```

*Após a execução, um menu será exibido no terminal.*

## Opções do Menu

### Opção 1 — Câmera ao Vivo

Conecta à câmera Atlas SWIR e exibe o vídeo infravermelho com um mapa de calor numérico em falsa cor.

Durante a visualização, é possível pressionar `C` para registrar imagens da bancada.

### Opção 2 — Comparação em Pasta

Analisa todas as fotos presentes na pasta `fotos_comparar/`.

O sistema encontra a referência matemática mais próxima em tons de cinza e exibe o resultado visualmente lado a lado na tela.

## Finalização

Ao finalizar qualquer uma das opções pressionando `ESC`, o sistema compila os cálculos em um arquivo Excel `.xlsx`, utilizado como relatório de inspeção.

Os relatórios gerados podem ser:

```text
relatorio_swir_camera.xlsx
relatorio_swir_pasta.xlsx
```

## 📊 Estrutura do Relatório Gerado

O arquivo Excel gerado ao final de cada execução contém colunas estruturadas para fins acadêmicos e analíticos.

| Coluna | Descrição |
|---|---|
| Origem | Indica se a leitura veio do fluxo ao vivo da câmera ou do processamento local de arquivos. |
| Arquivo | Nome da imagem salva ou analisada. |
| Brilho (Raw) | Intensidade matemática média obtida diretamente do canal infravermelho em tons de cinza. Representa o dado puro. |
| Referência Mais Próxima | Arquivo da pasta de calibração que obteve o menor desvio absoluto de intensidade. |
| Brilho da Ref | Intensidade infravermelha correspondente à imagem de referência calibrada. |
| Diferença | Erro absoluto entre a amostra analisada e a referência do modelo. |

## Fluxo Geral do Sistema

1. Instale o Arena SDK.
2. Execute `python main.py`.
3. Escolha entre câmera ao vivo ou comparação em pasta.
4. Registre ou analise imagens SWIR.
5. Finalize com `ESC`.
6. Consulte o relatório Excel gerado.

## Observações

- As imagens de referência devem estar previamente calibradas com níveis de umidade conhecidos.
- A comparação é baseada na intensidade média em tons de cinza do canal infravermelho.
- O relatório final permite rastrear a origem, o arquivo analisado, a referência mais próxima e a diferença matemática entre amostra e referência.
