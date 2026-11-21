# PRD — Organizador de Etiquetas

## Original problem statement
Sistema web "Organizador de Etiquetas" para empresa de tintas (várias marcas/lojas na Shopee). Recebe PDF de etiquetas exportado pelo Up Seller, analisa cada etiqueta, identifica produto (SKU, marca, qualidade, cor, tamanho, quantidade) e reordena as páginas: QUALIDADE (1 ECON, 2 PISO PREMIUM/STANDARD, 3 MANTA EMB/SUPERLAV) → COR (sequência operacional de 27 cores: Branco Neve, Erva Doce, Rosa BB, Azul BB, Azul Céu, Lilás, Pink, Gelo, Palha, Marfim, Pérola, Baunilha, Amarelo, Areia, Bege, Algodão Egípcio, Papel Picado, Ovelha, Vermelho, Coloridas, Grafite, Asfalto, Inox, Cinza, Nanquim, Elefante, Crômio) → MARCA (MAISON, INV, NCC/NUANCE, CMC, DMC, VERT/VERTICE, NVL, MAGMA, MORALAR) → TAMANHO crescente numérico (sem converter peso↔volume sem regra). Seção REVISAR no final com motivo; correção manual; nenhuma página perdida; PDF original nunca alterado, só reordenado. Histórico, configurações editáveis no banco (marcas, cores, qualidades, variações, ordens, regras de tamanho). Classificação local, sem IA externa. Testar com o PDF real "etiquetas 2.pdf" e gerar relatório de teste.

User choices: sem login (sistema local aberto); histórico mostra todos os arquivos; não guardar PDFs no servidor (apenas download); NCC/NUANCE e VERT/VERTICE juntas como uma marca.

## Architecture
- Backend FastAPI + MongoDB. Motor em `backend/engine/` (text, extractor, classifier, organizer, defaults). PyMuPDF para leitura por coordenadas e `select()` para reordenar páginas.
- Original PDF kept in temp dir 24h (TEMP_RETENTION_HOURS) only for download; jobs collection stores metadata + extracted SKUs + corrections; settings collection (key=main).
- Frontend React + shadcn: Início (upload/resultado/revisão/prévia/últimos), /resultado/:id, Histórico, Configurações (tabs).

## User personas
- Funcionário de expedição: envia PDF, baixa organizado, corrige revisões.
- Responsável: ajusta marcas, cores, qualidades e regras.

## Implemented (2026-11-21)
- Leitura da tabela DANFE (texto girado), multi-produto → revisão, agrupamento de páginas por n/N.
- Classificação configurável; ordenação; PDF final com verificação de integridade (67/67 idênticas).
- Correção manual, reanalisar com configurações atuais, histórico com exclusão, configurações com mover/arrastar e restaurar padrão.
- Teste real: 67 páginas, 63 classificadas (94%), 4 revisar (36 INV-EXCLUSIVOO, 43 Preto sem cor cadastrada, 45 dois SKUs, 67 SELADOR sem qualidade). Relatório: /app/memory/relatorio_teste.md, script backend/tests/relatorio_etiquetas.py.

## Assumptions (editable in Configurações)
- Coloridas = Camurça, Verde Musgo, Verde Água, Marsala, Telha, Terra, Marrom, Petróleo. Cinza Grafite → Grafite. Branco → Branco Neve. INOVALAR- prefix → INV. INV-PREM → PISO PREMIUM/STANDARD. Regra 3,6 L ordena como 5 KG. Preto não mapeado.
- OCR não incluído: páginas sem texto vão para REVISAR.

## Backlog
- P1: OCR (Tesseract) para PDFs escaneados.
- P1: Qualidade para SELADOR; cor para Preto.
- P2: Página separadora opcional entre seções; login se for exposto fora da rede.

## Next tasks
- Validar com mais PDFs reais de outras marcas (CMC, NVL).
