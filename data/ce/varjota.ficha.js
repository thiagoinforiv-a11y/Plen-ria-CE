/* Ficha política de Varjota/CE — editável à mão.
 * selo: "confirmado" (oficial ou 2+ fontes independentes) | "declaracao" (fala de alguém)
 *       "uma-fonte" (sem segunda fonte) | "pesquisa" (com instituto e nº de registro) | "a-conferir"
 * Nunca registre como "pesquisa" um número sem instituto e registro. */
window.PLENARIA_FICHAS = window.PLENARIA_FICHAS || {};
window.PLENARIA_FICHAS["ce/varjota"] = {
  atualizado: "2026-10-30",
  observacao: "Levantamento por busca na web. Neste ambiente as páginas não puderam ser abertas por inteiro; os itens foram conferidos pelo resumo da busca e devem ser relidos na fonte quando o acesso for liberado.",

  // Conferência automática (scripts/verificar.py): fatos conhecidos que os dados TÊM de bater.
  // Se a base carregada contradizer qualquer item, a verificação falha e nada é publicado.
  referencias: {
    municipio: { ibge: "2313955", tse: "98574" },
    prefeitos: { 2000: "Gentil Magalhães", 2004: "Gentil Magalhães", 2008: "Rosa Cândida", 2012: "Rosa Paulino", 2016: "Célia", 2020: "Elmo Monte", 2024: "Elmo Monte" },
    vereadoresMaisVotados: { 2024: ["Rosa Paulino", "Eudes Mesquita", "Gonçalinho"] },
    ultimasEleicoes: { municipal: 2024, geral: 2026 },
  },

  poder: [
    {
      papel: "Prefeito",
      nome: "Elmo Monte",
      detalhe: "Francisco Elmo Bezerra Monte. Eleito em 2024 (mandato 2025–2028); já havia governado de 2021 a 2024.",
      selo: "confirmado",
      fontes: [
        { nome: "IBGE Cidades", url: "https://www.ibge.gov.br/cidades-e-estados/ce/varjota.html" },
        { nome: "Prefeitura", url: "https://varjota.ce.gov.br/gestores.php" },
        { nome: "Resultado 2024 (ND Mais)", url: "https://ndmais.com.br/eleicoes-2024/resultados/1turno/ce/varjota/" },
      ],
    },
    {
      papel: "Vice-prefeito",
      nome: "Erivaldo Mororó",
      detalhe: "José Erivaldo Soares Mororó. Anunciou rompimento com o prefeito em set/2026 (ver fatos).",
      selo: "confirmado",
      fontes: [
        { nome: "Aprece", url: "https://aprece.org.br/municipio/varjota/" },
        { nome: "Blog do Amaury Alencar", url: "https://www.blogdoamauryalencar.com.br/2026/09/vice-prefeito-de-varjota-erivaldo.html" },
      ],
    },
    {
      papel: "Câmara Municipal",
      nome: "11 vereadores · presidente Roberto do Garrone",
      detalhe: "11ª legislatura (2025–2028). Composição base × oposição ainda não levantada.",
      selo: "confirmado",
      fontes: [{ nome: "Portal da Câmara", url: "https://camaravarjota.ce.gov.br/parlamentares/" }],
    },
    {
      papel: "Aprovação do prefeito",
      nome: "Nenhuma pesquisa registrada encontrada",
      detalhe: "Busca feita em 22/10/2026.",
      selo: "a-conferir",
      fontes: [],
    },
  ],

  acompanhar: [
    {
      titulo: "ADI 8036 (PDT) — sobras eleitorais no STF",
      status: "Sem decisão",
      porque: "Pelo cálculo do PDT, sairiam AJ Albuquerque (PP), Dr. Acilon (PSB) e Célio Studart (PSD). Atinge o federal ligado ao vice e a bancada do PSB (Denis Bezerra).",
      fontes: [{ nome: "Conjur", url: "https://conjur.com.br/2026-out-23/pdt-questiona-no-stf-regras-de-distribuicao-de-sobras-eleitorais-nas-eleicoes-proporcionais/" }],
    },
    {
      titulo: "Investigação eleitoral sobre Yury do Paredão (PF/TRE-CE)",
      status: "Em andamento · sem denúncia",
      porque: "Yury foi o federal mais votado em Varjota. Uma eventual ação contra o mandato mexe com a oposição local.",
      fontes: [{ nome: "Diário do Nordeste", url: "https://diariodonordeste.verdesmares.com.br/pontopoder/yury-do-paredao-e-alvo-de-operacao-da-pf-que-investiga-ilicitos-eleitorais-1.3795705" }],
    },
    {
      titulo: "Suplência de Danniel Oliveira (MDB) na Assembleia",
      status: "1º suplente · 81.259 votos",
      porque: "Assume se o deputado estadual do MDB sair. Daria à oposição de Varjota um deputado estadual em exercício.",
      fontes: [{ nome: "O Povo", url: "https://www.opovo.com.br/noticias/politica/eleicoes/2026/10/08/veja-suplentes-de-deputado-estadual-de-todos-os-partidos-no-ce.html" }],
    },
    {
      titulo: "Suplência de Denis Bezerra (PSB) na Câmara",
      status: "2º suplente · 40.405 votos",
      porque: "Precisa de duas vagas abertas no PSB. Cai de posição se a ação das sobras tirar uma cadeira do partido.",
      fontes: [{ nome: "O Povo", url: "https://www.opovo.com.br/noticias/politica/eleicoes/2026/10/07/veja-suplentes-de-deputado-federal-de-todos-os-partidos-no-ce.html" }],
    },
  ],

  fatos: [
    {
      data: "2026-10-04",
      titulo: "Yury do Paredão (MDB) reeleito com 261.291 votos, 3º mais votado do Ceará",
      resumo: "Foi o candidato a federal que ficou em 1º no maior número de municípios cearenses. Eleito em 2022 pelo PL, migrou para o MDB.",
      selo: "confirmado",
      fontes: [
        { nome: "O Povo", url: "https://mais.opovo.com.br/reportagens-especiais/resultado-legislativo-eleicoes-2026/2026/10/05/eleicoes-2026-quem-foram-os-deputados-federais-mais-votados-no-ceara.html" },
        { nome: "O Povo (comparativo 2022–2026)", url: "https://mais.opovo.com.br/jornal/politica/2026/10/16/sete-deputados-federais-do-ceara-ampliam-votacao-entre-2022-e-2026-e-cinco-perdem-votos.html" },
      ],
    },
    {
      data: "2026-10-04",
      titulo: "Lia Gomes (PSB) reeleita deputada estadual; 3.504 votos em Varjota",
      resumo: "54.433 votos no estado.",
      selo: "uma-fonte",
      fontes: [{ nome: "Hub Político", url: "https://hubpolitico.com.br/eleicoes/2026/apuracao/ce/deputado-estadual/candidato/liagomes" }],
    },
    {
      data: "2026-10-04",
      titulo: "Danniel Oliveira (MDB) fica como 1º suplente estadual, com 81.259 votos",
      resumo: "Atribuiu a não reeleição à votação fraca de colega de chapa. Tem base em Varjota (2.462 votos na cidade em 2022).",
      selo: "confirmado",
      fontes: [
        { nome: "O Povo", url: "https://www.opovo.com.br/noticias/politica/eleicoes/2026/10/13/deputado-atribui-nao-reeleicao-a-votacao-de-colega-da-chapa.html" },
        { nome: "Anuário do Ceará", url: "https://www.anuariodoceara.com.br/guia-das-cidades/fichas-dos-municipios/varjota/" },
      ],
    },
    {
      data: "2026-10-02",
      titulo: "PF faz buscas na casa de Yury do Paredão em investigação eleitoral",
      resumo: "14 mandados autorizados pelo TRE-CE, a pedido da Procuradoria Regional Eleitoral, em Fortaleza, Juazeiro do Norte e Barbalha. A defesa diz que nada foi apreendido na casa dele e que a apuração envolve material de campanha.",
      nota: "Sem denúncia, prisão ou decisão judicial até 30/10. Operação não significa culpa.",
      selo: "confirmado",
      fontes: [
        { nome: "O Povo", url: "https://www.opovo.com.br/noticias/politica/eleicoes/2026/10/02/pf-cumpre-14-mandados-em-investigacao-eleitoral-no-ceara.html" },
        { nome: "Metrópoles", url: "https://www.metropoles.com/colunas/tacio-lorran/deputado-yury-do-paredao-e-alvo-de-operacao-da-policia-federal" },
        { nome: "CN7 (versão do deputado)", url: "https://cn7.com.br/yury-do-paredao-confirma-busca-da-pf-em-residencia-e-afirma-que-nada-foi-apreendido/" },
      ],
    },
    {
      data: "2026-10-23",
      titulo: "PDT leva ao STF a regra das sobras (ADI 8036, relator Gilmar Mendes)",
      resumo: "Ação contra o art. 109 do Código Eleitoral (cálculo das 'maiores médias'), com pedido de liminar. No Ceará, 7 das 22 vagas federais de 2026 saíram das sobras. Pelo cálculo do próprio PDT, entrariam André Figueiredo (PDT), Renato Roseno (PSOL) e Sandrinha Cavalcante (Cidadania); sairiam Dr. Acilon (PSB), AJ Albuquerque (PP) e Célio Studart (PSD).",
      nota: "A ação existe e está no STF (várias fontes). Os nomes de quem entra e sai são cálculo do PDT, não do TSE. Sem decisão até 30/10. Efeito em Varjota depende de quanto a cidade votou em cada um desses nomes (dado do TSE ainda não carregado).",
      selo: "confirmado",
      fontes: [
        { nome: "Conjur", url: "https://conjur.com.br/2026-out-23/pdt-questiona-no-stf-regras-de-distribuicao-de-sobras-eleitorais-nas-eleicoes-proporcionais/" },
        { nome: "Gazeta do Povo", url: "https://www.gazetadopovo.com.br/eleicoes/2026/gilmar-recebe-acao-do-pdt-que-pode-mudar-calculo-de-cadeiras-na-camara/" },
        { nome: "O Povo (Vertical)", url: "https://mais.opovo.com.br/colunistas/vertical/2026/10/29/acao-pode-alterar-bancada-federal-do-ceara.html" },
      ],
    },
    {
      data: "2026-10-07",
      titulo: "Denis Bezerra (PSB) fica como 2º suplente federal, com 40.405 votos",
      resumo: "Atrás de Roger Aguiar (106.170) na lista de suplentes do PSB. Só assume se abrir vaga na bancada do PSB.",
      nota: "Se a ação das sobras tirar uma vaga do PSB, o deputado que sair passa a disputar a suplência e Denis tende a cair de posição.",
      selo: "uma-fonte",
      fontes: [{ nome: "O Povo", url: "https://www.opovo.com.br/noticias/politica/eleicoes/2026/10/07/veja-suplentes-de-deputado-federal-de-todos-os-partidos-no-ce.html" }],
    },
    {
      data: "2026-10-04",
      titulo: "Yury do Paredão é o deputado federal mais votado em Varjota",
      resumo: "Levantamento do O Povo com o 1º colocado para deputado federal em cada município cearense coloca Varjota entre as 24 cidades vencidas por Yury do Paredão.",
      nota: "Os votos exatos na cidade virão do TSE.",
      selo: "uma-fonte",
      fontes: [{ nome: "O Povo", url: "https://www.opovo.com.br/noticias/politica/eleicoes/2026/10/16/veja-os-deputados-federais-mais-votados-em-cada-estado.html" }],
    },
    {
      data: "2026-09",
      titulo: "Vice-prefeito Erivaldo Mororó anuncia rompimento com Elmo Monte",
      resumo: "Anúncio pelas redes sociais. Cita afastamento desde o início do mandato, dificuldade de contato com o prefeito e ausência do nome em placas de inauguração; o apoio dele a Ciro Gomes também pesou. Diz que não vai procurar a oposição e que vai trabalhar pelo seu candidato a deputado. Integrava o grupo desde 2008.",
      nota: "O texto diz 'neste domingo (08)', mas 8/9/2026 caiu numa terça; data exata a confirmar. Falta a versão do prefeito e quais vereadores acompanharam o vice.",
      selo: "uma-fonte",
      fontes: [{ nome: "Blog do Amaury Alencar", url: "https://www.blogdoamauryalencar.com.br/2026/09/vice-prefeito-de-varjota-erivaldo.html" }],
    },
    {
      data: "2024-10-06",
      titulo: "Vereadores mais votados em 2024: Rosa Paulino (1.774), Eudes Mesquita (992) e Gonçalinho (915)",
      resumo: "Os três foram eleitos para a legislatura 2025–2028.",
      selo: "confirmado",
      fontes: [
        { nome: "Anuário do Ceará", url: "https://www.anuariodoceara.com.br/guia-das-cidades/fichas-dos-municipios/varjota/" },
        { nome: "Câmara de Varjota (Rosa Paulino)", url: "https://camaravarjota.ce.gov.br/parlamentares/30/perfil/" },
        { nome: "ND+ (dados do TSE)", url: "https://ndmais.com.br/eleicoes-2024/resultados/1turno/ce/varjota/" },
      ],
    },
    {
      data: "",
      titulo: "MP Eleitoral pediu cassação de prefeito e vice-prefeita eleitos em Varjota",
      resumo: "Pedido por abuso de poder econômico e compra de votos.",
      nota: "Data não identificada. A menção a 'vice-prefeita' indica que pode ser de outro mandato, e não da chapa atual. Não usar antes de ler a matéria.",
      selo: "a-conferir",
      fontes: [{ nome: "MPCE", url: "https://mpce.mp.br/mp-eleitoral-pede-cassacao-de-diplomas-de-prefeito-e-vice-prefeita-eleitos-em-varjota-por-abuso-de-poder-economico-e-compra-de-votos/" }],
    },
  ],
};
