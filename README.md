# Organizador de Etiquetas

Reordena as páginas de PDFs de etiquetas do Up Seller na ordem **QUALIDADE → COR → MARCA → TAMANHO**.
As etiquetas que não puderem ser identificadas vão para a seção **REVISAR**, no final. Nenhuma página é alterada nem descartada.

## Estrutura
```
backend/
  server.py                 API FastAPI (rotas /api/...)
  engine/                   motor de organização (sem dependência da interface)
    text.py                 normalização (acentos, maiúsculas, espaços)
    extractor.py            leitura do PDF (PyMuPDF) e da tabela SKU/Descrição/Variação/QTD do DANFE
    classifier.py           regras de marca, qualidade, cor e tamanho
    organizer.py            ordenação e montagem do PDF final (só reordena páginas)
    defaults.py             marcas, cores, qualidades e regras de tamanho iniciais
  tests/relatorio_etiquetas.py   relatório de teste: python tests/relatorio_etiquetas.py arquivo.pdf saida.md
frontend/                   interface React (Início, Histórico, Configurações)
```

## Como o motor lê as etiquetas
1. Para cada página, localiza o cabeçalho da tabela do DANFE (SKU, Descrição, Variação, QTD) pela posição das palavras (funciona com texto girado).
2. Cada linha de produto é delimitada pela quantidade (QTD). Mais de um SKU diferente na mesma etiqueta → REVISAR.
3. Marca = prefixo exato do SKU (ex.: `NCC-`, `NUANCE-`, `INOVALAR-`). Prefixos parecidos não são aceitos.
4. Qualidade = primeiro trecho após a marca (`PISO2`, `ECON0`, `EMBO`, `MANTA18KG`...). Se faltar, procura na descrição (só se houver exatamente uma qualidade).
5. Tamanho = número + unidade no SKU (KG, KILOS, G, L, ML); a coluna Variação é usada como apoio e para detectar conflitos.
6. Cor = variações cadastradas no SKU (comparação sem acentos e sem espaços); a coluna Variação confirma ou indica conflito.
7. Páginas com a mesma numeração `n/N` (ou uma página sem numeração logo após uma numerada) ficam juntas.

## Executar localmente
Requisitos: Python 3.11+, Node 18+ e Yarn, MongoDB.
```
cd backend
pip install -r requirements.txt
# backend/.env: MONGO_URL, DB_NAME, CORS_ORIGINS, MAX_UPLOAD_MB, TEMP_RETENTION_HOURS
uvicorn server:app --host 0.0.0.0 --port 8001

cd frontend
# frontend/.env: REACT_APP_BACKEND_URL=http://IP-DO-SERVIDOR:8001
yarn install
yarn build        # gera a pasta build/ para servir em produção
yarn start        # modo desenvolvimento (porta 3000)
```

## Disponibilizar na rede da empresa
1. Instale em um computador/servidor fixo da rede e reserve um IP fixo (ex.: 192.168.0.10).
2. Rode o backend com `--host 0.0.0.0` (porta 8001) e sirva a pasta `frontend/build` (ex.: Nginx), com `REACT_APP_BACKEND_URL=http://192.168.0.10:8001` antes do `yarn build`.
3. Libere as portas no firewall do servidor. Os funcionários acessam `http://192.168.0.10` no navegador.
4. Não exponha o sistema para a internet: ele não possui login (uso interno, conforme solicitado).

## Privacidade
- Os PDFs são processados somente no servidor; nada é enviado para serviços externos.
- O PDF original fica em pasta temporária apenas por `TEMP_RETENTION_HOURS` (24 h) para permitir o download; o histórico guarda só os números e os SKUs lidos.
