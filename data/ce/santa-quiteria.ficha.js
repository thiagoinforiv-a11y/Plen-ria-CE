/* Ficha política de Santa Quitéria/CE — editável à mão. Comece pelas referências: elas conferem os dados do TSE. */
window.PLENARIA_FICHAS = window.PLENARIA_FICHAS || {};
window.PLENARIA_FICHAS["ce/santa-quiteria"] = {
  atualizado: "2026-11-05",
  observacao: "Na eleição ordinária de 2024, Braguinha (PSB) foi reeleito; teve o mandato cassado e Joel Barroso (PSB), seu filho, venceu a eleição suplementar de 26/10/2025. O arquivo do TSE de 2024 traz as duas eleições juntas — o importador agora guarda só a ordinária.",
  referencias: {
    municipio: { ibge: "2312205", tse: "15458" },
    prefeitos: { 2024: "Braguinha" },
    ultimasEleicoes: { municipal: 2024, geral: 2026 },
    interrupcoes: [{ eleicao: 2024, nome: "Braguinha", motivo: "cassado pela Justiça Eleitoral", curto: "cassado", depois: "Em outubro de dois mil e vinte e cinco, Joel Barroso venceu a eleição suplementar.", atual: "Joel Barroso", quando: "out/2025" }],
  },
  poder: [],
  fatos: [
    {
      data: "2025-10-26",
      titulo: "Joel Barroso (PSB) vence a eleição suplementar para prefeito",
      resumo: "Eleição convocada após a cassação de Braguinha, reeleito em 2024. Joel, filho de Braguinha, governava interinamente desde janeiro de 2025 como presidente da Câmara. Concorreram também Cândida Figueiredo (União) e Lígia Protásio (PT).",
      selo: "confirmado",
      fontes: [
        { nome: "Diário do Nordeste", url: "https://diariodonordeste.verdesmares.com.br/pontopoder/joel-barroso-e-eleito-prefeito-de-santa-quiteria-apos-cassacao-do-pai-1.3703305" },
        { nome: "O Povo", url: "https://mais.opovo.com.br/jornal/politica/2025/10/27/santa-quiteria-escolhe-em-nova-eleicao-o-filho-de-ex-prefeito-acusado-de-vinculo-com-faccao.html" },
      ],
    },
  ],
};
