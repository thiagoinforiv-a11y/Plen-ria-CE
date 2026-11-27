/* Ficha política de Pacujá/CE — editável à mão.
 * selo: "confirmado" (oficial ou 2+ fontes independentes) | "declaracao" (fala de alguém)
 *       "uma-fonte" (sem segunda fonte) | "pesquisa" (com instituto e nº de registro) | "a-conferir" */
window.PLENARIA_FICHAS = window.PLENARIA_FICHAS || {};
window.PLENARIA_FICHAS["ce/pacuja"] = {
  atualizado: "2026-11-05",
  observacao: "Levantamento por busca na web; os itens foram conferidos pelo resumo da busca e devem ser relidos na fonte.",

  // Conferência automática: se os dados carregados contradisserem algo aqui, a verificação falha.
  referencias: {
    municipio: { ibge: "2309904", tse: "14990" },
    prefeitos: { 2012: "Lucivane", 2016: "Alex Melo", 2024: "Pedro Allan" },
    ultimasEleicoes: { municipal: 2024, geral: 2026 },
    // mandatos interrompidos (entram no vídeo de histórico)
    interrupcoes: [{ eleicao: 2020, nome: "Raimundo Filho", motivo: "cassado por abuso de poder econômico", curto: "cassado" }],
  },

  poder: [
    {
      papel: "Prefeito",
      nome: "Pedro Allan",
      detalhe: "PSB. Eleito em 2024 com 71,43% dos votos válidos, aos 21 anos; mandato 2025–2028. Vice: Milena Melo (PT).",
      selo: "confirmado",
      fontes: [
        { nome: "Diário do Nordeste", url: "https://diariodonordeste.verdesmares.com.br/pontopoder/quem-ganhou-a-eleicao-2024-para-prefeito-em-pacuja-1.3566956" },
        { nome: "O Povo", url: "https://mais.opovo.com.br/jornal/politica/2024/10/17/com-60-anos-de-diferenca-quem-sao-e-o-que-querem-o-prefeito-mais-novo-e-mais-velho-do-ceara.html" },
      ],
    },
    {
      papel: "Vice-prefeita",
      nome: "Milena Melo",
      detalhe: "PT. Eleita em 2024 na chapa de Pedro Allan. Em 03/11/2026 anunciou que deixa o grupo político da gestão.",
      selo: "declaracao",
      fontes: [{ nome: "Instagram @milenamelopacuja", url: "https://www.instagram.com/milenamelopacuja/" }],
    },
  ],

  fatos: [
    {
      data: "2026-11-03",
      titulo: "Ex-prefeito Alex Melo e vice-prefeita Milena Melo anunciam saída do grupo da gestão municipal",
      resumo: "Em vídeos, Alex disse que a decisão foi refletida e amadurecida e que, segundo ele, o povo não está sendo tratado com a prioridade e o respeito que merece; o post fala em oposição responsável. Milena disse que sua história não começou na vice-prefeitura e que encerra o ciclo com serenidade. No mesmo dia, Raimundo Filho publicou vídeo dizendo que o contato do grupo com o povo é olho no olho, com trabalho e com verdade. O prefeito Pedro Allan não havia se manifestado até então.",
      selo: "declaracao",
      cartao2028: ["A gestão perdeu aliados", "ex-prefeito Alex Melo e a vice Milena deixaram o grupo (nov/2026)"],
      fontes: [
        { nome: "Instagram @alexmelopacuja", url: "https://www.instagram.com/alexmelopacuja/" },
        { nome: "Instagram @milenamelopacuja", url: "https://www.instagram.com/milenamelopacuja/" },
        { nome: "Instagram @raimundofilhorf", url: "https://www.instagram.com/raimundofilhorf/" },
      ],
    },
    {
      data: "2024-10-06",
      titulo: "Pedro Allan (PSB) é eleito prefeito com 71,43% contra João Paulo da Elma (Cidadania)",
      selo: "confirmado",
      fontes: [
        { nome: "Diário do Nordeste", url: "https://diariodonordeste.verdesmares.com.br/pontopoder/quem-ganhou-a-eleicao-2024-para-prefeito-em-pacuja-1.3566956" },
        { nome: "TRE-CE (totalização)", url: "https://www.tre-ce.jus.br/eleicao/eleicoes-2024/arquivos-totalizacao/relatorios-da-totalizacao/pacuja-relatorio-do-resultado-da-totalizacao-2024" },
      ],
    },
    {
      data: "2024-09",
      titulo: "Cassação confirmada; Câmara elege Rodrigo Carvalho (PP) prefeito até 31/12/2024",
      resumo: "Com a cassação de Raimundo Filho e do vice mantida, o TSE determinou eleição indireta pela Câmara Municipal. Jandson Pessoa (Republicanos) foi escolhido vice.",
      selo: "confirmado",
      fontes: [
        { nome: "Diário do Nordeste", url: "https://diariodonordeste.verdesmares.com.br/pontopoder/apos-cassacao-de-prefeito-e-vice-pacuja-elege-novo-gestor-para-mandato-ate-31-de-dezembro-de-2024-1.3575302" },
        { nome: "O Povo", url: "https://www.opovo.com.br/noticias/politica/2024/09/12/tse-confirma-que-camara-de-pacuja-elegera-imediatamente-prefeito-para-ir-ate-o-fim-do-ano.html" },
      ],
    },
    {
      data: "2023-02",
      titulo: "Eleição suplementar marcada para 5/2/2023 é suspensa pelo STF",
      resumo: "O ministro Alexandre de Moraes suspendeu a votação até o julgamento do recurso. Prefeito e vice voltaram ao cargo em dezembro de 2023.",
      selo: "uma-fonte",
      fontes: [{ nome: "Diário do Nordeste", url: "https://diariodonordeste.verdesmares.com.br/pontopoder/eleicao-suplementar-em-pacuja-no-ceara-e-suspensa-pelo-ministro-alexandre-de-morais-1.3330749" }],
    },
    {
      data: "2022-06",
      titulo: "TRE-CE cassa Raimundo Filho, eleito em 2020, por abuso de poder econômico",
      resumo: "Prefeito e vice eleitos em 2020 foram cassados por compra de votos e abuso de poder econômico (Operação Mensalinho).",
      selo: "confirmado",
      fontes: [
        { nome: "Diário do Nordeste", url: "https://diariodonordeste.verdesmares.com.br/pontopoder/prefeito-e-vice-de-pacuja-sao-cassados-por-abuso-de-poder-economico-nas-eleicoes-de-2020-1.3250283" },
        { nome: "Diário do Nordeste (TRE mantém)", url: "https://diariodonordeste.verdesmares.com.br/pontopoder/tre-ce-mantem-cassacao-de-prefeitos-de-iguatu-e-de-pacuja-novas-eleicoes-serao-convocadas-1.3293189" },
      ],
    },
    {
      data: "2020-11-15",
      titulo: "Raimundo Filho é eleito prefeito aos 24 anos, o mais jovem do Ceará em 2020",
      selo: "uma-fonte",
      fontes: [{ nome: "O Povo (raio-x dos 184 prefeitos)", url: "https://mais.opovo.com.br/reportagens-especiais/eleicoes-2020-ceara/2020/11/29/raio-x-dos-184-prefeitos-do-ceara.html" }],
    },
  ],
};
