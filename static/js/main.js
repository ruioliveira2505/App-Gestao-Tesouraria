import { abrirDrillDownCategoria, abrirDrillDownGrupo, alternarExpandirTodos, atualizarIconeExpandirRecolher, carregarAnalise, fecharDrillDown, ordenarRecorrentes, toggleGrupo, trocarAbaAnalise, trocarModoDrilldown, trocarTipo } from './analise.js'
import { abrirEsqueciPassword, enviarEsqueciPassword, fazerLogin, fazerRegisto, iniciarDetecaoInatividade, logout, submeterRedefinicao, trocarTab, verificarTokenReset } from './auth.js'
import { aplicarPresetCalendarioRange, calendarioEstado, calendarioRangeEstado, fecharCalendarioRange, fecharCalendarioSimples, iniciarPickerAnalise, iniciarPickerContaData, iniciarPickerContas, iniciarPickerMovData, iniciarPickerMovimentos, iniciarPickerReconciliacao, mudarAnoCalendario, mudarMesCalendario, navegarCalendario, primeiroDiaMes, selecionarDiaCalendarioRange, selecionarDiaCalendarioSimples } from './calendario.js'
import { abrirEditarConta, abrirModalAjusteSaldo, abrirModalConta, carregarContas, eliminarConta, eliminarReconciliacao, esconderFormReconciliacao, fecharModalReconciliacoes, fecharSeletorMoeda, guardarConta, guardarReconciliacao, mostrarFormReconciliacao, ordenarContas, toggleLinhaExpandida, toggleSeletorMoeda } from './contas.js'
import { ICONE_INFO, ICONE_OLHO_ABERTO, ICONE_OLHO_FECHADO, ICONE_PERFIL_CATEGORIAS, ICONE_PERFIL_GERAL, ICONE_PREFERENCIAS, ICONE_SAIR, ICONE_SEGURANCA, ICONE_SETA_DIREITA, ICONE_UTILIZADOR, estadoGlobal } from './estado.js'
import { fecharFiltroCat, fecharFiltroCategoriaMov, fecharFiltroConta, fecharFolhaFiltros, fecharMenusAcoes, fecharSeletorCategoriaMovForm, fecharSeletorContaForm, fecharSeletorTipoMovForm, fecharTodosOsFiltros, limparFiltroContaSelecao, limparFiltroSeccaoMovimentos, limparFiltrosAnalise, limparFiltrosContas, limparFiltrosMovimentos, renderizarFiltroCategoriaEspaco, renderizarFiltroConta, selecionarTodasCategoriaFiltroArvore, selecionarTodasContasFiltro, toggleFiltroCat, toggleFiltroCategoriaMov, toggleFiltroConta, toggleFolhaFiltros, toggleMenuAcoesConta, toggleMenuAcoesMovimento, toggleMenuAcoesReconciliacao, toggleSeletorCategoriaMovForm, toggleSeletorConta, toggleSeletorTipoMovForm } from './filtros.js'
import { aplicarTraducoes, t } from './i18n.js'
import { abrirEditarMovimento, abrirModalMovimento, atualizarBadgePendentes, carregarMovimentos, confirmarMovimento, confirmarTodosPendentes, eliminarMovimento, filtrarApenasPendentes, guardarMovimento, limparModoPendentes, ordenarMovimentos, renderizarTabelaMovimentosDebounced } from './movimentos.js'
import { fecharOrdenar, selecionarCampoOrdenar, selecionarDirecaoOrdenar, toggleOrdenar } from './ordenacao.js'
import { abrirEditarCategoriaGestao, abrirEditarGrupo, abrirModalAlterarPassword, abrirModalCategoria, abrirModalEditarPerfil, abrirModalGrupo, arrastarFim, arrastarInicio, arrastarSobre, carregarConfiguracoes, confirmarEliminacaoComMigracao, confirmarEliminacaoForcada, confirmarEliminarCategoria, eliminarContaUtilizador, guardarCategoriaGestao, guardarGrupo, guardarPassword, guardarPerfil, largarSobre, moverItemCategoria, terminarTodasAsSessoes, toggleMenuAcoesCategoria, toggleMenuAcoesGrupo, trocarSecaoPerfil, trocarTipoCategorias } from './perfil.js'
import { ligarValidacaoFormulario, mostrarAjudaAoEscrever } from './ui.js'
import { api, attrJs, carregarFiltrosSalvos, comBotaoDesativado, fecharModal, isoDateStr } from './utils.js'

// exposicao global das funcoes referenciadas via onclick/onchange/oninput/ondrag*/ondrop no HTML
window.abrirDrillDownCategoria = abrirDrillDownCategoria
window.abrirDrillDownGrupo = abrirDrillDownGrupo
window.abrirEditarCategoriaGestao = abrirEditarCategoriaGestao
window.abrirEditarConta = abrirEditarConta
window.abrirEditarGrupo = abrirEditarGrupo
window.abrirEditarMovimento = abrirEditarMovimento
window.abrirEsqueciPassword = abrirEsqueciPassword
window.abrirModalAjusteSaldo = abrirModalAjusteSaldo
window.abrirModalAlterarPassword = abrirModalAlterarPassword
window.abrirModalCategoria = abrirModalCategoria
window.abrirModalConfiguracoes = abrirModalConfiguracoes
window.abrirModalConta = abrirModalConta
window.abrirModalEditarPerfil = abrirModalEditarPerfil
window.abrirModalGrupo = abrirModalGrupo
window.abrirModalMovimento = abrirModalMovimento
window.acionarFabMobile = acionarFabMobile
window.alternarExpandirTodos = alternarExpandirTodos
window.alternarOcultarValores = alternarOcultarValores
window.alternarVisibilidadePassword = alternarVisibilidadePassword
window.aplicarPresetCalendarioRange = aplicarPresetCalendarioRange
window.arrastarFim = arrastarFim
window.arrastarInicio = arrastarInicio
window.arrastarSobre = arrastarSobre
window.attrJs = attrJs
window.comBotaoDesativado = comBotaoDesativado
window.confirmarEliminacaoComMigracao = confirmarEliminacaoComMigracao
window.confirmarEliminacaoForcada = confirmarEliminacaoForcada
window.confirmarEliminarCategoria = confirmarEliminarCategoria
window.confirmarMovimento = confirmarMovimento
window.confirmarTodosPendentes = confirmarTodosPendentes
window.eliminarConta = eliminarConta
window.eliminarContaUtilizador = eliminarContaUtilizador
window.eliminarMovimento = eliminarMovimento
window.eliminarReconciliacao = eliminarReconciliacao
window.enviarEsqueciPassword = enviarEsqueciPassword
window.esconderFormReconciliacao = esconderFormReconciliacao
window.fazerLogin = fazerLogin
window.fazerRegisto = fazerRegisto
window.fecharDrillDown = fecharDrillDown
window.fecharFolhaFiltros = fecharFolhaFiltros
window.fecharMenusAcoes = fecharMenusAcoes
window.fecharModal = fecharModal
window.fecharModalConfiguracoes = fecharModalConfiguracoes
window.fecharModalReconciliacoes = fecharModalReconciliacoes
window.filtrarApenasPendentes = filtrarApenasPendentes
window.guardarCategoriaGestao = guardarCategoriaGestao
window.guardarConta = guardarConta
window.guardarGrupo = guardarGrupo
window.guardarMovimento = guardarMovimento
window.guardarPassword = guardarPassword
window.guardarPerfil = guardarPerfil
window.guardarReconciliacao = guardarReconciliacao
window.irPara = irPara
window.largarSobre = largarSobre
window.limparFiltroContaSelecao = limparFiltroContaSelecao
window.limparFiltroSeccaoMovimentos = limparFiltroSeccaoMovimentos
window.limparFiltrosAnalise = limparFiltrosAnalise
window.limparFiltrosContas = limparFiltrosContas
window.limparFiltrosMovimentos = limparFiltrosMovimentos
window.limparModoPendentes = limparModoPendentes
window.logout = logout
window.mostrarFormReconciliacao = mostrarFormReconciliacao
window.moverItemCategoria = moverItemCategoria
window.mudarAnoCalendario = mudarAnoCalendario
window.mudarMesCalendario = mudarMesCalendario
window.mudarLingua = mudarLingua
window.mudarTema = mudarTema
window.navegarCalendario = navegarCalendario
window.ordenarContas = ordenarContas
window.ordenarMovimentos = ordenarMovimentos
window.ordenarRecorrentes = ordenarRecorrentes
window.renderizarFiltroCategoriaEspaco = renderizarFiltroCategoriaEspaco
window.renderizarFiltroConta = renderizarFiltroConta
window.renderizarTabelaMovimentosDebounced = renderizarTabelaMovimentosDebounced
window.selecionarCampoOrdenar = selecionarCampoOrdenar
window.selecionarDiaCalendarioRange = selecionarDiaCalendarioRange
window.selecionarDiaCalendarioSimples = selecionarDiaCalendarioSimples
window.selecionarDirecaoOrdenar = selecionarDirecaoOrdenar
window.selecionarTodasCategoriaFiltroArvore = selecionarTodasCategoriaFiltroArvore
window.selecionarTodasContasFiltro = selecionarTodasContasFiltro
window.submeterRedefinicao = submeterRedefinicao
window.terminarTodasAsSessoes = terminarTodasAsSessoes
window.toggleFiltroCat = toggleFiltroCat
window.toggleFiltroCategoriaMov = toggleFiltroCategoriaMov
window.toggleFiltroConta = toggleFiltroConta
window.toggleFolhaFiltros = toggleFolhaFiltros
window.toggleFriso = toggleFriso
window.toggleGrupo = toggleGrupo
window.toggleLinhaExpandida = toggleLinhaExpandida
window.toggleMenuAcoesCategoria = toggleMenuAcoesCategoria
window.toggleMenuAcoesConta = toggleMenuAcoesConta
window.toggleMenuAcoesGrupo = toggleMenuAcoesGrupo
window.toggleMenuAcoesMovimento = toggleMenuAcoesMovimento
window.toggleMenuAcoesReconciliacao = toggleMenuAcoesReconciliacao
window.toggleMenuAvatar = toggleMenuAvatar
window.toggleOrdenar = toggleOrdenar
window.toggleSeletorCategoriaMovForm = toggleSeletorCategoriaMovForm
window.toggleSeletorConta = toggleSeletorConta
window.toggleSeletorMoeda = toggleSeletorMoeda
window.toggleSeletorTipoMovForm = toggleSeletorTipoMovForm
window.trocarAbaAnalise = trocarAbaAnalise
window.trocarModoDrilldown = trocarModoDrilldown
window.trocarSecaoPerfil = trocarSecaoPerfil
window.trocarTab = trocarTab
window.trocarTipo = trocarTipo
window.trocarTipoCategorias = trocarTipoCategorias

// INICIALIZAÇÃO E NAVEGAÇÃO
// ═══════════════════════════════════════════════════════════
export async function iniciarApp() {
  document.getElementById("auth-screen").style.display = "none"
  atualizarAvatar()
  aplicarTema()
  if (localStorage.getItem("frisoExpandido") === "true") document.getElementById("friso").classList.add("expandido")
  document.getElementById("icone-menu-olho").innerHTML = estadoGlobal.valoresOcultos ? ICONE_OLHO_FECHADO : ICONE_OLHO_ABERTO
  document.getElementById("texto-menu-olho").textContent = estadoGlobal.valoresOcultos ? t("menu.mostrar_valores") : t("menu.ocultar_valores")
  const pagina = localStorage.getItem("paginaAtual") || "contas"
  ativarPagina(["contas", "movimentos", "analise"].includes(pagina) ? pagina : "contas")
  document.getElementById("app-screen").style.display = "block"
  estadoGlobal.contasCache = await api("/contas")
  estadoGlobal.categoriasCache    = await api("/categorias")
  estadoGlobal.arvoreAnaliseCache = await api("/categorias/arvore")
  restaurarFiltros()
  iniciarPickerContas()
  iniciarPickerAnalise()
  iniciarPickerMovimentos()
  iniciarPickerMovData()
  iniciarPickerReconciliacao()
  iniciarPickerContaData()
  carregarPagina(pagina)
  atualizarBadgePendentes()
  iniciarDetecaoInatividade()
}

function restaurarFiltros() {
  const hoje      = isoDateStr(new Date())
  const inicioMes = isoDateStr(primeiroDiaMes())

  const ct = carregarFiltrosSalvos("contas")
  estadoGlobal.ctDataDe  = (ct?.dataDe)  || inicioMes
  estadoGlobal.ctDataAte = (ct?.dataAte) || hoje
  if (ct?.contas?.length) estadoGlobal.contasSelecionadas.ct = new Set(ct.contas)

  const an = carregarFiltrosSalvos("analise")
  estadoGlobal.anDataDe  = (an?.dataDe)  || inicioMes
  estadoGlobal.anDataAte = (an?.dataAte) || hoje
  if (an?.contas?.length) estadoGlobal.contasSelecionadas.an = new Set(an.contas)
  if (an?.categorias?.length) estadoGlobal.categoriasSelecionadas = new Set(an.categorias)

  const mv = carregarFiltrosSalvos("movimentos")
  estadoGlobal.movDataDe  = (mv?.dataDe)  || inicioMes
  estadoGlobal.movDataAte = (mv?.dataAte) || hoje
  if (mv?.categorias?.length) estadoGlobal.categoriasMovSelecionadas = new Set(mv.categorias)
  if (mv?.contas?.length) estadoGlobal.contasSelecionadas.mov = new Set(mv.contas)

  renderizarFiltroConta("ct")
  renderizarFiltroConta("an")
  renderizarFiltroConta("mov")
  renderizarFiltroCategoriaEspaco("an")
  renderizarFiltroCategoriaEspaco("mov")
}

function ativarPagina(pagina) {
  document.querySelector("main").scrollTop = 0
  document.querySelectorAll(".page").forEach(p => p.classList.remove("active"))
  document.querySelectorAll(".friso-item[data-pagina]").forEach(l => l.classList.toggle("active", l.dataset.pagina === pagina))
  document.getElementById("page-" + pagina)?.classList.add("active")
  if (pagina === "analise") trocarAbaAnalise(localStorage.getItem("analise_aba") || "resumo")   // ← novo
  atualizarBarraMobile(pagina)
  setTimeout(() => atualizarPosicoesFixas("page-" + pagina), 0)
}
const TITULOS_PAGINAS_MOBILE = { contas: () => t("friso.contas"), movimentos: () => t("friso.movimentos"), analise: () => t("friso.analise") }
const ACOES_FAB_MOBILE = { contas: () => abrirModalConta(), movimentos: () => abrirModalMovimento() }
let fabAcaoAtual = null
function atualizarBarraMobile(pagina) {
  document.getElementById("titulo-pagina-mobile").textContent = TITULOS_PAGINAS_MOBILE[pagina]?.() || ""
  fabAcaoAtual = ACOES_FAB_MOBILE[pagina] || null
  document.getElementById("fab-mobile-adicionar").style.display = fabAcaoAtual ? "flex" : "none"
}
export function acionarFabMobile() { if (fabAcaoAtual) fabAcaoAtual() }
export function toggleFriso() {
  const expandido = !document.getElementById("friso").classList.contains("expandido")
  document.getElementById("friso").classList.toggle("expandido", expandido)
  localStorage.setItem("frisoExpandido", expandido)
}
function carregarPagina(pagina) {
  if (pagina === "contas")     carregarContas()
  if (pagina === "analise")    carregarAnalise()
  if (pagina === "movimentos") carregarMovimentos()
}
export function irPara(pagina) { ativarPagina(pagina); localStorage.setItem("paginaAtual", pagina); carregarPagina(pagina) }
function iniciaisNome(nome) {
  if (!nome) return "?"
  const partes = nome.trim().split(/\s+/)
  const primeira = partes[0][0] || ""
  const ultima = partes.length > 1 ? partes[partes.length - 1][0] : ""
  return (primeira + ultima).toUpperCase()
}
export function atualizarAvatar() {
  document.getElementById("avatar-btn").textContent = iniciaisNome(estadoGlobal.NOME)
  const nomeEl = document.getElementById("friso-nome-utilizador")
  if (nomeEl) nomeEl.textContent = estadoGlobal.NOME
}
export function abrirModalConfiguracoes() {
  fecharMenuAvatar()
  document.getElementById("friso").classList.remove("expandido")
  trocarSecaoPerfil("conta")
  document.getElementById("modal-configuracoes").classList.add("open")
  document.querySelector(".perfil-sidebar").scrollLeft = 0
  carregarConfiguracoes()
}
export function fecharModalConfiguracoes() {
  document.getElementById("modal-configuracoes").classList.remove("open")
}

let avatarMenuAberto = false
export function toggleMenuAvatar(e) {
  e.stopPropagation()
  const estavaAberto = avatarMenuAberto
  fecharTodosOsFiltros()
  avatarMenuAberto = !estavaAberto
  const menu = document.getElementById("avatar-menu")
  menu.classList.toggle("aberto", avatarMenuAberto)
  if (avatarMenuAberto) {
    const rect = document.getElementById("avatar-wrapper").getBoundingClientRect()
    const larguraMenu = 200
    const cabeADireita = rect.right + 8 + larguraMenu <= window.innerWidth
    menu.style.top = "auto"
    menu.style.bottom = (window.innerHeight - rect.bottom) + "px"
    if (cabeADireita) {
      menu.style.left = (rect.right + 8) + "px"
      menu.style.right = "auto"
    } else {
      menu.style.left = "auto"
      menu.style.right = (window.innerWidth - rect.right) + "px"
    }
  }
}
function aplicarTema() {
  const salvo = localStorage.getItem("tema") || "sistema"
  const escuro = salvo === "escuro" || (salvo === "sistema" && window.matchMedia("(prefers-color-scheme: dark)").matches)
  if (escuro) document.documentElement.setAttribute("data-tema", "escuro")
  else document.documentElement.removeAttribute("data-tema")
  document.querySelectorAll("#toggle-tema button").forEach(b => b.classList.remove("active"))
  document.getElementById("tema-" + salvo)?.classList.add("active")
}
export function mudarTema(tema) {
  localStorage.setItem("tema", tema)
  aplicarTema()
  carregarPagina(localStorage.getItem("paginaAtual") || "contas")
}
window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
  if ((localStorage.getItem("tema") || "sistema") === "sistema") aplicarTema()
})
export function mudarLingua(lingua) {
  estadoGlobal.lingua = lingua
  localStorage.setItem("lingua", lingua)
  aplicarTraducoes()
  carregarPagina(localStorage.getItem("paginaAtual") || "contas")
}
export function fecharMenuAvatar() {
  avatarMenuAberto = false
  document.getElementById("avatar-menu")?.classList.remove("aberto")
}

export function alternarOcultarValores() {
  estadoGlobal.valoresOcultos = !estadoGlobal.valoresOcultos
  localStorage.setItem("valoresOcultos", estadoGlobal.valoresOcultos)
  const icone = document.getElementById("icone-menu-olho")
  icone.innerHTML = estadoGlobal.valoresOcultos ? ICONE_OLHO_FECHADO : ICONE_OLHO_ABERTO
  document.getElementById("texto-menu-olho").textContent = estadoGlobal.valoresOcultos ? t("menu.mostrar_valores") : t("menu.ocultar_valores")
  carregarPagina(localStorage.getItem("paginaAtual") || "contas")
}
export function alternarVisibilidadePassword(idCampo, botao) {
  const input = document.getElementById(idCampo)
  const aRevelar = input.type === "password"
  input.type = aRevelar ? "text" : "password"
  botao.innerHTML = aRevelar ? ICONE_OLHO_ABERTO : ICONE_OLHO_FECHADO
  botao.setAttribute("aria-label", aRevelar ? t("auth.ocultar_password") : t("auth.mostrar_password"))
}

// ═══════════════════════════════════════════════════════════
// ARRANQUE
// ═══════════════════════════════════════════════════════════
aplicarTraducoes()
document.querySelectorAll(".toggle-password").forEach(btn => { btn.innerHTML = ICONE_OLHO_FECHADO; btn.setAttribute("aria-label", t("auth.mostrar_password")) })
document.getElementById("icone-sidebar-conta").innerHTML = ICONE_UTILIZADOR
document.getElementById("icone-sidebar-seguranca").innerHTML = ICONE_SEGURANCA
document.getElementById("icone-sidebar-categorias").innerHTML = ICONE_PERFIL_CATEGORIAS
document.getElementById("icone-sidebar-preferencias").innerHTML = ICONE_PREFERENCIAS
document.getElementById("icone-menu-config").innerHTML = ICONE_PERFIL_GERAL
document.getElementById("icone-menu-sair").innerHTML = ICONE_SAIR
document.getElementById("conta-saldo-ajuda").innerHTML = ICONE_INFO
document.getElementById("reconc-titulo-ajuda").innerHTML = ICONE_INFO
document.getElementById("seta-perfil-avatar").innerHTML = ICONE_SETA_DIREITA
document.getElementById("seta-perfil-email").innerHTML = ICONE_SETA_DIREITA
document.getElementById("seta-perfil-password").innerHTML = ICONE_SETA_DIREITA
document.getElementById("seta-perfil-sessoes").innerHTML = ICONE_SETA_DIREITA
document.getElementById("reconc-valor-ajuda").innerHTML = ICONE_INFO
document.getElementById("reconc-data-ajuda").innerHTML = ICONE_INFO
document.getElementById("conta-data-ajuda").innerHTML = ICONE_INFO
mostrarAjudaAoEscrever("reg-password", "ajuda-reg-password")
mostrarAjudaAoEscrever("perfil-pw-nova", "ajuda-perfil-pw-nova")
mostrarAjudaAoEscrever("reset-password-nova", "ajuda-reset-password-nova")
ligarValidacaoFormulario(["login-email", "login-password"], "btn-login")
ligarValidacaoFormulario(["reg-nome", "reg-email", "reg-password"], "btn-registo")
ligarValidacaoFormulario(["esqueci-email"], "btn-esqueci")
atualizarIconeExpandirRecolher()

document.addEventListener("click", e => {
  const path = e.composedPath()
  const btn   = document.getElementById("filtro-cat-btn")
  const panel = document.getElementById("filtro-cat-panel")
  if (!path.includes(btn) && !path.includes(panel)) fecharFiltroCat()

  const movCatBtn = document.getElementById("mov-filtro-categoria-btn"), movCatPanel = document.getElementById("mov-filtro-categoria-panel")
  if (movCatBtn && !path.includes(movCatBtn) && !path.includes(movCatPanel)) fecharFiltroCategoriaMov()

  const movContaPanel = document.getElementById("mov-conta-panel"), movContaInput = document.getElementById("mov-conta-wrapper")
  if (movContaPanel && !path.includes(movContaPanel) && !path.includes(movContaInput)) fecharSeletorContaForm()

  const movCategoriaFormPanel = document.getElementById("mov-categoria-panel"), movCategoriaFormInput = document.getElementById("mov-categoria-wrapper")
  if (movCategoriaFormPanel && !path.includes(movCategoriaFormPanel) && !path.includes(movCategoriaFormInput)) fecharSeletorCategoriaMovForm()

  const movTipoPanel = document.getElementById("mov-tipo-panel"), movTipoInput = document.getElementById("mov-tipo-wrapper")
  if (movTipoPanel && !path.includes(movTipoPanel) && !path.includes(movTipoInput)) fecharSeletorTipoMovForm()

  const ctContaBtn = document.getElementById("ct-filtro-conta-btn"), ctContaPanel = document.getElementById("ct-filtro-conta-panel")
  if (ctContaBtn && !path.includes(ctContaBtn) && !path.includes(ctContaPanel)) fecharFiltroConta("ct")

  const anContaBtn = document.getElementById("an-filtro-conta-btn"), anContaPanel = document.getElementById("an-filtro-conta-panel")
  if (anContaBtn && !path.includes(anContaBtn) && !path.includes(anContaPanel)) fecharFiltroConta("an")

  const movFiltroContaBtn = document.getElementById("mov-filtro-conta-btn"), movFiltroContaPanel = document.getElementById("mov-filtro-conta-panel")
  if (movFiltroContaBtn && !path.includes(movFiltroContaBtn) && !path.includes(movFiltroContaPanel)) fecharFiltroConta("mov")

  const movOrdenarBtn = document.getElementById("mov-ordenar-btn"), movOrdenarPanel = document.getElementById("mov-ordenar-panel")
  if (movOrdenarBtn && !path.includes(movOrdenarBtn) && !path.includes(movOrdenarPanel)) fecharOrdenar("mov")

  const ctOrdenarBtn = document.getElementById("ct-ordenar-btn"), ctOrdenarPanel = document.getElementById("ct-ordenar-panel")
  if (ctOrdenarBtn && !path.includes(ctOrdenarBtn) && !path.includes(ctOrdenarPanel)) fecharOrdenar("ct")

  if (calendarioEstado) {
    const calInput = document.getElementById(calendarioEstado.inputId + "-wrapper") || document.getElementById(calendarioEstado.inputId)
    const calPanel = document.getElementById("calendario-panel")
    if (calInput && !path.includes(calInput) && !path.includes(calPanel)) fecharCalendarioSimples()
  }
  if (calendarioRangeEstado) {
    const calInput = document.getElementById(calendarioRangeEstado.inputId + "-wrapper") || document.getElementById(calendarioRangeEstado.inputId)
    const calPanel = document.getElementById("calendario-range-panel")
    if (calInput && !path.includes(calInput) && !path.includes(calPanel)) fecharCalendarioRange()
  }

  const anRecOrdenarBtn = document.getElementById("an-recorrentes-ordenar-btn"), anRecOrdenarPanel = document.getElementById("an-recorrentes-ordenar-panel")
  if (anRecOrdenarBtn && !path.includes(anRecOrdenarBtn) && !path.includes(anRecOrdenarPanel)) fecharOrdenar("an-recorrentes")

  const avatarBtn = document.getElementById("avatar-wrapper"), avatarMenu = document.getElementById("avatar-menu")
  if (avatarBtn && !path.includes(avatarBtn) && !path.includes(avatarMenu)) fecharMenuAvatar()

  const contaMoedaPanel = document.getElementById("conta-moeda-panel"), contaMoedaInput = document.getElementById("conta-moeda-wrapper")
  if (contaMoedaPanel && !path.includes(contaMoedaPanel) && !path.includes(contaMoedaInput)) fecharSeletorMoeda()
})

const observadorModaisTelaCheia = new MutationObserver(() => {
  const frisoAbertoEmMobile = window.innerWidth <= 768 && document.getElementById("friso").classList.contains("expandido")
  const algumAberto = document.querySelector(".modal-tela-cheia.open") !== null || document.querySelector(".folha-filtros-overlay.aberta") !== null || frisoAbertoEmMobile
  document.querySelector("#page-contas .filtros")?.classList.toggle("folha-aberta", algumAberto)
  document.querySelector("#page-contas .ordenacao-mobile")?.classList.toggle("folha-aberta", algumAberto)
  document.querySelector("#page-movimentos .filtros")?.classList.toggle("folha-aberta", algumAberto)
  document.querySelector("#page-movimentos .ordenacao-mobile")?.classList.toggle("folha-aberta", algumAberto)
  document.querySelector("#page-analise .filtros")?.classList.toggle("folha-aberta", algumAberto)
  document.querySelector("#page-analise .ordenacao-mobile")?.classList.toggle("folha-aberta", algumAberto)
  const main = document.querySelector("main")
  if (algumAberto && !bloqueioScrollAtivo) {
    const rect = main.getBoundingClientRect()
    scrollAntesDoBloqueio = main.scrollTop
    main.style.position = "fixed"
    main.style.top = "0"
    main.style.left = rect.left + "px"
    main.style.width = rect.width + "px"
    main.style.height = "100dvh"
    main.style.overflow = "hidden"
    main.style.zIndex = "70"
    bloqueioScrollAtivo = true
  } else if (!algumAberto && bloqueioScrollAtivo) {
    main.style.position = ""
    main.style.top = ""
    main.style.left = ""
    main.style.width = ""
    main.style.height = ""
    main.style.overflow = ""
    main.style.zIndex = ""
    main.scrollTop = scrollAntesDoBloqueio
    bloqueioScrollAtivo = false
  }
})
let scrollAntesDoBloqueio = 0
let bloqueioScrollAtivo = false
document.addEventListener("touchmove", (e) => {
  if (!bloqueioScrollAtivo) return
  const dentroDeModalAberto = e.target.closest(".modal-tela-cheia.open, .folha-filtros-overlay.aberta, .filtros-conteudo.aberta, .friso.expandido")
  if (!dentroDeModalAberto) e.preventDefault()
}, { passive: false })
document.querySelectorAll(".modal-tela-cheia, .folha-filtros-overlay, #friso").forEach(m => {
  observadorModaisTelaCheia.observe(m, { attributes: true, attributeFilter: ["class"] })
})
document.addEventListener("blur", (e) => {
  if (!e.target.matches?.("input, select, textarea")) return
  if (!e.target.closest(".modal-tela-cheia")) return
  const main = document.querySelector("main")
  setTimeout(() => main.scrollTo(main.scrollLeft, main.scrollTop), 100)
}, true)
const PAGINAS_COM_POSICOES_FIXAS = ["page-contas", "page-movimentos", "page-analise"]
export function atualizarPosicoesFixas(idPagina) {
  const pagina = document.getElementById(idPagina)
  if (!pagina || !pagina.classList.contains("active")) return
  const emMobile = window.innerWidth <= 768
  const referencia = emMobile ? document.querySelector(".barra-mobile-topo") : pagina.querySelector(".cabecalho-pagina")
  const topoBase = referencia ? referencia.getBoundingClientRect().height : 0
  const filtros = pagina.querySelector(".filtros")
  if (!filtros) return
  filtros.style.top = topoBase + "px"
  const alturaFiltros = topoBase + filtros.getBoundingClientRect().height
  pagina.querySelectorAll("thead th").forEach(th => th.style.top = alturaFiltros + "px")
  const ordenar = pagina.querySelector(".ordenacao-mobile")
  if (ordenar) ordenar.style.top = alturaFiltros + "px"
}
function atualizarTodasPosicoesFixas() {
  PAGINAS_COM_POSICOES_FIXAS.forEach(atualizarPosicoesFixas)
}
const observadorPosicoesFixas = new ResizeObserver(atualizarTodasPosicoesFixas)
window.addEventListener("load", () => {
  observadorPosicoesFixas.observe(document.querySelector(".barra-mobile-topo"))
  PAGINAS_COM_POSICOES_FIXAS.forEach(idPagina => {
    const pagina = document.getElementById(idPagina)
    observadorPosicoesFixas.observe(pagina.querySelector(".cabecalho-pagina"))
    observadorPosicoesFixas.observe(pagina.querySelector(".filtros"))
  })
})
window.addEventListener("resize", atualizarTodasPosicoesFixas)

if (!verificarTokenReset() && estadoGlobal.TOKEN) iniciarApp()
