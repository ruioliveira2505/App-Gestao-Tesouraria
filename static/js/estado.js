// ═══════════════════════════════════════════════════════════
// ESTADO GLOBAL
// ═══════════════════════════════════════════════════════════
export const API = ""

// Estado partilhado por toda a app — um objecto só (mutável nas suas propriedades) em vez
// de ~37 variáveis "let" soltas. Faz falta quando isto for dividido em módulos ES: mutar
// uma propriedade de um objecto importado é sempre permitido; reatribuir directamente uma
// variável importada não é (só o módulo que a declara pode fazê-lo). Usar sempre
// "estadoGlobal.propriedade", nunca desestruturar para uma variável solta e reatribuí-la.
export let estadoGlobal = {
  TOKEN: localStorage.getItem("token"),
  NOME:  localStorage.getItem("nome"),

  contasCache:           [],
  categoriasCache:       [],
  perfilCache:           {},
  gruposCache:           [],
  arvoreCategoriasCache: [],  // perfil — gestão de categorias
  arvoreAnaliseCache:    [],  // análise — filtro de categorias
  movimentosCache:       [],
  reconciliacoesCache:   [],

  tipoAtual:            "in",
  tipoGestaoCategorias: "in",
  moedaAnaliseGlobal:   "EUR",
  lingua:               localStorage.getItem("lingua") || "pt",
  valoresOcultos:       localStorage.getItem("valoresOcultos") === "true",
  gruposExpandidos:     false,
  pendentesAtivo:       false,
  filtroCatAberto:      false,
  categoriasSelecionadas: new Set(),
  categoriasMovSelecionadas: new Set(),
  contasSelecionadas: { ct: new Set(), an: new Set(), mov: new Set() },

  graficos: {},
  analiseCache: { mensal: null },

  anDataDe: undefined, anDataAte: undefined,
  movDataDe: null, movDataAte: null,
  ctDataDe:  null, ctDataAte:  null,

  ordenacaoContas:        { campo: "nome", direcao: 1 },
  contasTabelaCache:      [],
  ordenacaoMovimentos:    { campo: "data", direcao: -1 },
  movimentosTabelaCache:  [],
  ordenacaoRecorrentes:   { campo: "proxima_data_estimada", direcao: 1 },
  recorrentesTabelaCache: [],

  elimAtual: null,

  drilldownAtual: null,

  timerInatividade: null,
}
export const linhaVerticalPlugin = {
  id: "linhaVertical",
  afterDraw: (chart) => {
    const ativo = chart.tooltip?.getActiveElements()
    if (!ativo || !ativo.length) return
    const { ctx, chartArea } = chart
    const x = ativo[0].element.x
    ctx.save()
    ctx.beginPath()
    ctx.setLineDash([4, 4])
    ctx.moveTo(x, chartArea.top)
    ctx.lineTo(x, chartArea.bottom)
    ctx.lineWidth = 1
    ctx.strokeStyle = corTema("rgba(26,26,26,0.25)", "rgba(255,255,255,0.3)")
    ctx.stroke()
    ctx.restore()
  }
}

export const TEMPO_INATIVIDADE_MS = 15 * 60 * 1000
export const EVENTOS_ATIVIDADE = ["mousemove", "keydown", "click", "scroll", "touchstart"]

export const BANCOS_PT_COMUNS  = ["Caixa Geral de Depósitos","Millennium BCP","Novo Banco","Santander Totta","BPI","Crédito Agrícola","ActivoBank","Bankinter","Banco CTT","Revolut"]
export const TIPOS_CONTA_COMUNS = ["Conta Corrente","Conta Poupança","Conta a Prazo","Numerário"]

export const PALETA_VERDE    = ["#2f9e64","#4cb47c","#6fc696","#94d7b1","#bce4cc","#5cb886"]
export const PALETA_VERMELHA = ["#d9584a","#e17567","#e9958a","#f0b7ae","#f6d9d4","#e0685a"]
// ═══════════════════════════════════════════════════════════
// ÍCONES (SVG inline)
// ═══════════════════════════════════════════════════════════
export const ICONE_OLHO_ABERTO       = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8Z"></path><circle cx="12" cy="12" r="3"></circle></svg>`
export const ICONE_OLHO_FECHADO      = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9.88 9.88a3 3 0 1 0 4.24 4.24"></path><path d="M10.73 5.08A10.43 10.43 0 0 1 12 5c7 0 11 8 11 8a13.16 13.16 0 0 1-1.67 2.68"></path><path d="M6.61 6.61A13.526 13.526 0 0 0 1 13s4 8 11 8a9.74 9.74 0 0 0 5.39-1.61"></path><line x1="2" y1="2" x2="22" y2="22"></line></svg>`

export const ICONE_PROTEGIDA         = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>`
export const ICONE_TOAST_SUCESSO     = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"></path></svg>`
export const ICONE_TOAST_ERRO        = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>`
export const ICONE_ORDENAR_NEUTRO    = `<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M8 9l4-4 4 4"></path><path d="M16 15l-4 4-4-4"></path></svg>`
export const ICONE_ORDENAR_ASC       = `<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 19V5"></path><path d="M5 12l7-7 7 7"></path></svg>`
export const ICONE_ORDENAR_DESC      = `<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 5v14"></path><path d="M19 12l-7 7-7-7"></path></svg>`
export const ICONE_PERFIL_GERAL      = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>`
export const ICONE_PERFIL_CATEGORIAS = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20.59 13.41 11 3.83A2 2 0 0 0 9.59 3.24L4 3a1 1 0 0 0-1 1l.24 5.59a2 2 0 0 0 .59 1.41l9.58 9.58a2 2 0 0 0 2.83 0l4.35-4.35a2 2 0 0 0 0-2.83Z"></path><circle cx="7.5" cy="7.5" r="1.5"></circle></svg>`
export const ICONE_SETA_BAIXO        = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 9l6 6 6-6"></path></svg>`
export const ICONE_SETA_CIMA         = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 15l-6-6-6 6"></path></svg>`
export const ICONE_INFO              = `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>`
export const ICONE_ARRASTAR          = `<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" stroke="none"><circle cx="9" cy="6" r="1.5"/><circle cx="15" cy="6" r="1.5"/><circle cx="9" cy="12" r="1.5"/><circle cx="15" cy="12" r="1.5"/><circle cx="9" cy="18" r="1.5"/><circle cx="15" cy="18" r="1.5"/></svg>`
export const ICONE_GRAFICO           = `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>`
export const ICONE_CHECK = `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"></path></svg>`
export const ICONE_SETA_DIREITA = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18l6-6-6-6"></path></svg>`
export function corTema(clara, escura) {
  return document.documentElement.getAttribute("data-tema") === "escuro" ? escura : clara
}
export const ICONE_INDETERMINADO = `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="6" y1="12" x2="18" y2="12"></line></svg>`
export const ICONE_PREFERENCIAS = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="4" y1="21" x2="4" y2="14"></line><line x1="4" y1="10" x2="4" y2="3"></line><line x1="12" y1="21" x2="12" y2="12"></line><line x1="12" y1="8" x2="12" y2="3"></line><line x1="20" y1="21" x2="20" y2="16"></line><line x1="20" y1="12" x2="20" y2="3"></line><line x1="1" y1="14" x2="7" y2="14"></line><line x1="9" y1="8" x2="15" y2="8"></line><line x1="17" y1="16" x2="23" y2="16"></line></svg>`
export const ICONE_SAIR = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path><polyline points="16 17 21 12 16 7"></polyline><line x1="21" y1="12" x2="9" y2="12"></line></svg>`
export const ICONE_UTILIZADOR = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>`
export const ICONE_SEGURANCA = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>`

// ═══════════════════════════════════════════════════════════
