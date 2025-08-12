## Simulador de Incêndio Florestal com Elevação e Umidade
Este projeto é uma simulação baseada em autômatos celulares que modela a propagação de um incêndio florestal. Diferente de modelos simples, esta simulação incorpora fatores ambientais como a elevação do terreno e a umidade da vegetação para criar uma representação mais realista e dinâmica do comportamento do fogo.

![run-simulation.gif]

## Conceitos Principais
A simulação é construída sobre os princípios de autômatos celulares, onde uma grade de células evolui ao longo do tempo com base em um conjunto de regras simples. Cada célula em nossa grade representa um pedaço de terra e possui três características principais:

**1. Estado**: O que a célula é atualmente (ÁRVORE, QUEIMANDO, QUEIMADA ou VAZIA).

**2. Elevação**: A altitude da célula, que cria um terreno virtual.

**3. Umidade**: O teor de umidade da célula se for uma árvore, tornando-a mais difícil ou mais fácil de pegar fogo.

O propósito do projeto é simular como esses fatores influenciam a propagação do fogo, criando padrões complexos e imprevisíveis a partir de regras simples e locais.

## Como Funciona: Baseado no Automato Celular
O projeto é uma aplicação de um autômato celular 2D e layers que trazem consigo caracteristicas para cada uma das células.

**A Grade 2D:** O mapa é definido por uma grade 2D, onde cada index da grade é uma célula. O estado das célula é determinado por suas próprias propriedades e pelo estado de seus vizinhos(vizinhança de von Neumann: cima, baixo, esquerda, direita).

**Estrutura de Dados da Célula:** Para armazenar múltiplas informações em cada célula, a estrutura de dados foi transformada. Utilizando o NumPy, um array 2D convencional foi expandido para uma grade 3D (linhas x colunas x 3). Isso permite que cada célula (x, y) funcione como um vetor, contendo suas propriedades fundamentais em "camadas":

`grid[y, x, 0]`: O Estado (ÁRVORE, QUEIMANDO, etc.).

`grid[y, x, 1]`: A Elevação.

`grid[y, x, 2]`: A Umidade.

**Regras de Transição**: A cada "passo" da simulação, uma nova grade é calculada com base na atual, aplicando estas regras a cada célula:

**1. Se uma célula está QUEIMANDO:** No próximo passo, ela se torna QUEIMADA. Esta é uma mudança de estado simples e incondicional.

**2. Se uma célula é uma ÁRVORE:** Ela verifica seus quatro vizinhos. Se algum vizinho estiver QUEIMANDO, a árvore tem uma chance de pegar fogo. 
> Essa chance não é fixa; é calculada dinamicamente com base em:

    Umidade: A umidade interna da árvore (1 - umidade) reduz a probabilidade base de ignição. Uma árvore mais úmida tem menos probabilidade de queimar.

**3. Diferença de Elevação:**

**3.1. Propagação Morro Acima**: Se a árvore está em uma elevação maior que o fogo (elevacao_arvore > elevacao_fogo), a probabilidade é significativamente aumentada (* MULTIPLICADOR_SUBIDA). Isso simula como o calor sobe e pré-aquece o combustível acima.

**3.2. Propagação Morro Abaixo:** Se a árvore está em uma elevação menor, a probabilidade é ligeiramente diminuída (* MULTIPLICADOR_DESCIDA), pois a propagação é menos eficiente.