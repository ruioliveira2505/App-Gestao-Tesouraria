import { carregarAnalise } from './analise.js'
import { fecharCalendarioRange, fecharCalendarioSimples, iniciarPickerAnalise, iniciarPickerContas, iniciarPickerMovimentos, primeiroDiaMes } from './calendario.js'
import { abrirEditarConta, abrirModalAjusteSaldo, atualizarSombraScrollReconciliacoes, carregarContas, eliminarConta, eliminarReconciliacao, fecharSeletorMoeda, mostrarFormReconciliacao } from './contas.js'
import { BANCOS_PT_COMUNS, ICONE_CHECK, ICONE_INDETERMINADO, TIPOS_CONTA_COMUNS, estadoGlobal } from './estado.js'
import { nomeCategoria, t } from './i18n.js'
import { fecharMenuAvatar } from './main.js'
import { abrirEditarMovimento, carregarMovimentos, eliminarMovimento } from './movimentos.js'
import { fecharOrdenar } from './ordenacao.js'
import { toggleMenuAcoesCategoria, toggleMenuAcoesGrupo } from './perfil.js'
import { ligarValidacaoMovimento } from './ui.js'
import { escapeHtml, isoDateStr } from './utils.js'

// HELPERS: OPÇÕES DE CONTA E CATEGORIA
// ═══════════════════════════════════════════════════════════

export function opcoesBancos() { return [...new Set([...BANCOS_PT_COMUNS, ...estadoGlobal.contasCache.map(c => c.banco).filter(b => b && b.trim())])].sort() }
export function opcoesTipos() { return [...new Set([...TIPOS_CONTA_COMUNS, ...estadoGlobal.contasCache.map(c => c.tipo).filter(t => t && t.trim())])].sort() }

export function ligarCampoComSugestoesInline(idInput, getOpcoes) {
  const input = document.getElementById(idInput)
  input.addEventListener("input", (e) => {
    if (e.inputType && e.inputType.startsWith("delete")) return
    const valor = input.value
    if (!valor) return
    const opcoes = getOpcoes()
    const match = opcoes.find(o => o.toLowerCase().startsWith(valor.toLowerCase()) && o.toLowerCase() !== valor.toLowerCase())
    if (!match) return
    input.value = valor + match.slice(valor.length)
    input.setSelectionRange(valor.length, input.value.length)
  })
  input.addEventListener("keydown", (e) => {
    if (e.key === "Escape") input.value = input.value.slice(0, input.selectionStart)
  })
}

function atualizarCategoriasPorTipo() {
  document.getElementById("mov-categoria").value = ""
  document.getElementById("mov-categoria-display").value = ""
  renderizarSeletorCategoriaMovForm(null)
  ligarValidacaoMovimento()
}

// ─── Seletor de Conta (modal Movimento) ────────────────────
export function toggleSeletorConta(e) {
  e.stopPropagation()
  const painel = document.getElementById("mov-conta-panel")
  const estavaAberto = painel.classList.contains("aberto")
  fecharTodosOsFiltros()
  const abrir = !estavaAberto
  painel.classList.toggle("aberto", abrir)
  if (abrir) painel.scrollTop = 0
}
export function fecharSeletorContaForm() {
  document.getElementById("mov-conta-panel")?.classList.remove("aberto")
}

export function renderizarSeletorConta(selecionadoId) {
  const lista = document.getElementById("mov-conta-lista")
  lista.innerHTML = ""
  let bancoAtual = null
  const contasOrdenadas = [...estadoGlobal.contasCache].sort((a, b) => bancoOuSemBanco(a.banco).localeCompare(bancoOuSemBanco(b.banco)) || a.nome.localeCompare(b.nome))
  contasOrdenadas.forEach(c => {
    const chaveBanco = bancoOuSemBanco(c.banco)
    if (chaveBanco !== bancoAtual) {
      bancoAtual = chaveBanco
      const sep = document.createElement("div")
      sep.className = "seletor-grupo-label"
      sep.textContent = chaveBanco
      lista.appendChild(sep)
    }
    const row = document.createElement("div")
    row.className = "filtro-item-linha filtro-item-indentado" + (c.id === selecionadoId ? " selecionado" : "")
    row.innerHTML = `<span>${escapeHtml(c.nome)}</span><span class="check">${ICONE_CHECK}</span>`
    row.onclick = () => selecionarContaMovForm(c.id)
    lista.appendChild(row)
  })
}

export function selecionarContaMovForm(contaId) {
  document.getElementById("mov-conta").value = contaId
  const conta = estadoGlobal.contasCache.find(c => c.id === contaId)
  document.getElementById("mov-conta-display").value = conta ? conta.nome : ""
  renderizarSeletorConta(contaId)
  fecharSeletorContaForm()
  ligarValidacaoMovimento()
}

// ─── Seletor de Direção (modal Movimento) ────────────────
// função, não objecto — tem de reflectir sempre a língua actual, não a que estava em
// vigor quando o módulo carregou (ver t() em i18n.js).
const rotulosTipoMov = () => ({ in: t("generico.entrada"), out: t("generico.saida") })

export function toggleSeletorTipoMovForm(e) {
  e.stopPropagation()
  const painel = document.getElementById("mov-tipo-panel")
  const estavaAberto = painel.classList.contains("aberto")
  fecharTodosOsFiltros()
  const abrir = !estavaAberto
  painel.classList.toggle("aberto", abrir)
  if (abrir) painel.scrollTop = 0
}
export function fecharSeletorTipoMovForm() {
  document.getElementById("mov-tipo-panel")?.classList.remove("aberto")
}

export function renderizarSeletorTipoMovForm(selecionado) {
  const lista = document.getElementById("mov-tipo-lista")
  lista.innerHTML = ""
  const rotulos = rotulosTipoMov()
  ;["in", "out"].forEach(valor => {
    const row = document.createElement("div")
    row.className = "filtro-item-linha" + (valor === selecionado ? " selecionado" : "")
    row.innerHTML = `<span>${rotulos[valor]}</span><span class="check">${ICONE_CHECK}</span>`
    row.onclick = () => selecionarTipoMovForm(valor)
    lista.appendChild(row)
  })
}

export function selecionarTipoMovForm(valor) {
  document.getElementById("mov-tipo").value = valor
  document.getElementById("mov-tipo-display").value = rotulosTipoMov()[valor]
  renderizarSeletorTipoMovForm(valor)
  fecharSeletorTipoMovForm()
  atualizarCategoriasPorTipo()
}

// ─── Seletor de Categoria (modal Movimento) ────────────────
export function toggleSeletorCategoriaMovForm(e) {
  e.stopPropagation()
  const painel = document.getElementById("mov-categoria-panel")
  const estavaAberto = painel.classList.contains("aberto")
  fecharTodosOsFiltros()
  const abrir = !estavaAberto
  painel.classList.toggle("aberto", abrir)
  if (abrir) painel.scrollTop = 0
}
export function fecharSeletorCategoriaMovForm() {
  document.getElementById("mov-categoria-panel")?.classList.remove("aberto")
}

export function renderizarSeletorCategoriaMovForm(selecionadoId) {
  const lista = document.getElementById("mov-categoria-lista")
  lista.innerHTML = ""
  const tipo = document.getElementById("mov-tipo").value
  if (!tipo) {
    lista.innerHTML = `<div class="filtro-opcao-todas" style="cursor:default">${t("movimentos.escolhe_primeiro_o_tipo")}</div>`
    return
  }
  const grupos = estadoGlobal.arvoreAnaliseCache.filter(g => tipo === "in" ? g.eh_recebimento : !g.eh_recebimento)
  grupos.forEach(g => {
    const sep = document.createElement("div")
    sep.className = "seletor-grupo-label"
    sep.textContent = nomeCategoria(g.nome, g.slug)
    lista.appendChild(sep)
    g.categorias.forEach(c => {
      const row = document.createElement("div")
      row.className = "filtro-item-linha filtro-item-indentado" + (c.id === selecionadoId ? " selecionado" : "")
      row.innerHTML = `<span>${escapeHtml(nomeCategoria(c.nome, c.slug))}</span><span class="check">${ICONE_CHECK}</span>`
      row.onclick = () => selecionarCategoriaMovForm(c.id)
      lista.appendChild(row)
    })
  })
}

export function selecionarCategoriaMovForm(categoriaId) {
  document.getElementById("mov-categoria").value = categoriaId
  let nome = ""
  for (const g of estadoGlobal.arvoreAnaliseCache) {
    const c = g.categorias.find(c => c.id === categoriaId)
    if (c) { nome = nomeCategoria(c.nome, c.slug); break }
  }
  document.getElementById("mov-categoria-display").value = nome
  renderizarSeletorCategoriaMovForm(categoriaId)
  fecharSeletorCategoriaMovForm()
  ligarValidacaoMovimento()
}


export function toggleFolhaFiltros(prefixo) {
  document.getElementById(prefixo + "-filtros-conteudo").classList.add("aberta")
  document.getElementById(prefixo + "-folha-overlay").classList.add("aberta")
}
export function fecharFolhaFiltros(prefixo) {
  document.getElementById(prefixo + "-filtros-conteudo").classList.remove("aberta")
  document.getElementById(prefixo + "-folha-overlay").classList.remove("aberta")
}
function atualizarBadgeFiltrosMobile(prefixo, ativo) {
  const badge = document.getElementById(prefixo + "-badge-filtros-mobile")
  if (badge) badge.style.display = ativo ? "inline-flex" : "none"
}

// ─── Visibilidade do botão "Limpar filtros" ───────────────
export function atualizarVisibilidadeLimparContas() {
  const ehDefeito = estadoGlobal.contasSelecionadas.ct.size === 0 && estadoGlobal.ctDataDe === isoDateStr(primeiroDiaMes()) && estadoGlobal.ctDataAte === isoDateStr(new Date())
  document.getElementById("ct-filtros-limpar-linha").classList.toggle("escondido", ehDefeito)
  atualizarBadgeFiltrosMobile("ct", estadoGlobal.contasSelecionadas.ct.size > 0)
  document.getElementById("ct-limpar-seccao").classList.toggle("escondido", estadoGlobal.contasSelecionadas.ct.size === 0)
}
export function temFiltrosAnaliseAtivos() {
  return !!(estadoGlobal.contasSelecionadas.an.size > 0 || estadoGlobal.categoriasSelecionadas.size > 0 || estadoGlobal.anDataDe !== isoDateStr(primeiroDiaMes()) || estadoGlobal.anDataAte !== isoDateStr(new Date()))
}
export function atualizarVisibilidadeLimparAnalise() {
  const ativos = temFiltrosAnaliseAtivos()
  document.getElementById("an-filtros-limpar-linha").classList.toggle("escondido", !ativos)
  atualizarBadgeFiltrosMobile("an", ativos)
  document.getElementById("an-limpar-filtros-sheet").classList.toggle("escondido", !ativos)
}
function temFiltroSeccaoMovimentosAtivo() {
  return !!(estadoGlobal.contasSelecionadas.mov.size > 0 || estadoGlobal.categoriasMovSelecionadas.size > 0 || estadoGlobal.movDataDe !== isoDateStr(primeiroDiaMes()) || estadoGlobal.movDataAte !== isoDateStr(new Date()))
}
export function limparFiltroSeccaoMovimentos() {
  estadoGlobal.contasSelecionadas.mov.clear()
  estadoGlobal.categoriasMovSelecionadas.clear()
  const inputPesqConta = document.getElementById("mov-filtro-conta-pesquisa")
  if (inputPesqConta) inputPesqConta.value = ""
  const inputPesqCat = document.getElementById("mov-filtro-categoria-pesquisa")
  if (inputPesqCat) inputPesqCat.value = ""
  estadoGlobal.movDataDe = isoDateStr(primeiroDiaMes()); estadoGlobal.movDataAte = isoDateStr(new Date())
  renderizarFiltroCategoriaEspaco("mov")
  renderizarFiltroConta("mov")
  iniciarPickerMovimentos(); carregarMovimentos()
}
export function temFiltrosMovimentosAtivos() {
  return !!(estadoGlobal.contasSelecionadas.mov.size > 0 || estadoGlobal.categoriasMovSelecionadas.size > 0 || document.getElementById("filtro-pesquisa").value.trim() || estadoGlobal.pendentesAtivo || estadoGlobal.movDataDe !== isoDateStr(primeiroDiaMes()) || estadoGlobal.movDataAte !== isoDateStr(new Date()))
}
export function atualizarVisibilidadeLimparMovimentos() {
  document.getElementById("mov-filtros-limpar-linha").classList.toggle("escondido", !temFiltrosMovimentosAtivos())
  atualizarBadgeFiltrosMobile("mov", temFiltroSeccaoMovimentosAtivo())
  document.getElementById("mov-limpar-filtros-sheet").classList.toggle("escondido", !temFiltroSeccaoMovimentosAtivo())
}



// ─── Limpar filtros ───────────────────────────────────────
export function limparFiltroContaSelecao() {
  estadoGlobal.contasSelecionadas.ct.clear()
  const inputPesq = document.getElementById("ct-filtro-conta-pesquisa")
  if (inputPesq) inputPesq.value = ""
  renderizarFiltroConta("ct")
  carregarContas()
}
export function limparFiltrosContas() {
  estadoGlobal.contasSelecionadas.ct.clear()
  estadoGlobal.ctDataDe = isoDateStr(primeiroDiaMes()); estadoGlobal.ctDataAte = isoDateStr(new Date())
  localStorage.removeItem("filtros_contas")
  const inputPesq = document.getElementById("ct-filtro-conta-pesquisa")
  if (inputPesq) inputPesq.value = ""
  renderizarFiltroConta("ct")
  iniciarPickerContas(); carregarContas()
}
export function limparFiltrosAnalise() {
  estadoGlobal.contasSelecionadas.an.clear()
  estadoGlobal.anDataDe = isoDateStr(primeiroDiaMes()); estadoGlobal.anDataAte = isoDateStr(new Date())
  estadoGlobal.categoriasSelecionadas.clear()
  localStorage.removeItem("filtros_analise")
  const inputPesqConta = document.getElementById("an-filtro-conta-pesquisa")
  if (inputPesqConta) inputPesqConta.value = ""
  const inputPesqCat = document.getElementById("filtro-cat-pesquisa")
  if (inputPesqCat) inputPesqCat.value = ""
  renderizarFiltroConta("an")
  renderizarFiltroCategoriaEspaco("an")
  iniciarPickerAnalise(); carregarAnalise()
}
export function limparFiltrosMovimentos() {
  estadoGlobal.pendentesAtivo = false
  estadoGlobal.contasSelecionadas.mov.clear()
  estadoGlobal.categoriasMovSelecionadas.clear()
  document.getElementById("filtro-pesquisa").value = ""
  const inputPesqConta = document.getElementById("mov-filtro-conta-pesquisa")
  if (inputPesqConta) inputPesqConta.value = ""
  const inputPesqCat = document.getElementById("mov-filtro-categoria-pesquisa")
  if (inputPesqCat) inputPesqCat.value = ""
  estadoGlobal.movDataDe = isoDateStr(primeiroDiaMes()); estadoGlobal.movDataAte = isoDateStr(new Date())
  localStorage.removeItem("filtros_movimentos")
  renderizarFiltroCategoriaEspaco("mov")
  renderizarFiltroConta("mov")
  iniciarPickerMovimentos(); carregarMovimentos()
}


// nunca guardado numa const de topo: tem de reflectir sempre a língua actual, não a que
// estava em vigor quando o módulo carregou (ver t() em i18n.js).
function bancoOuSemBanco(banco) { return (banco && banco.trim()) ? banco : t("filtros.sem_banco") }
export function trOuTraco(v) { return (v && v.trim()) ? v : "—" }

// ═══════════════════════════════════════════════════════════
// FILTRO DE CONTAS
// ═══════════════════════════════════════════════════════════
// ─── Filtro de Conta, dois níveis por Banco (Contas/Análise/Movimentos) ───
export function toggleFiltroConta(prefixo, e) {
  e.stopPropagation()
  const painel = document.getElementById(prefixo + "-filtro-conta-panel")
  const estavaAberto = painel.classList.contains("aberto")
  fecharTodosOsFiltros()
  const btn = document.getElementById(prefixo + "-filtro-conta-btn")
  const abrir = !estavaAberto
  painel.classList.toggle("aberto", abrir)
  btn.classList.toggle("ativo", abrir)
  if (abrir) painel.scrollTop = 0
}
export function fecharFiltroConta(prefixo) {
  document.getElementById(prefixo + "-filtro-conta-panel").classList.remove("aberto")
  document.getElementById(prefixo + "-filtro-conta-btn").classList.remove("ativo")
}

function gruposContasPorBanco() {
  const bancos = {}
  estadoGlobal.contasCache.forEach(c => { const chave = bancoOuSemBanco(c.banco); (bancos[chave] ||= []).push(c) })
  const semBanco = t("filtros.sem_banco")
  return Object.keys(bancos).sort((a, b) => {
    if (a === semBanco) return 1
    if (b === semBanco) return -1
    return a.localeCompare(b)
  }).map(banco => ({
    banco, contas: bancos[banco].sort((a, b) => a.nome.localeCompare(b.nome))
  }))
}
export function renderizarFiltroConta(prefixo) {
  const lista = document.getElementById(prefixo + "-filtro-conta-lista")
  if (!lista) return
  lista.innerHTML = ""
  const selecionadas = estadoGlobal.contasSelecionadas[prefixo]
  const inputPesquisa = document.getElementById(prefixo + "-filtro-conta-pesquisa")
  const termo = (inputPesquisa ? inputPesquisa.value : "").trim().toLowerCase()

  gruposContasPorBanco().forEach(g => {
    const bancoBate = !termo || g.banco.toLowerCase().includes(termo)
    const contasVisiveis = bancoBate ? g.contas : g.contas.filter(c => c.nome.toLowerCase().includes(termo))
    if (termo && contasVisiveis.length === 0) return

    const idsGrupo = g.contas.map(c => c.id)
    const nSel = idsGrupo.filter(id => selecionadas.has(id)).length
    const completo = nSel === idsGrupo.length
    const parcial = nSel > 0 && !completo

    const grupoRow = document.createElement("div")
    grupoRow.className = "filtro-item-linha filtro-grupo-linha" + (completo ? " selecionado" : parcial ? " indeterminado" : "")
    grupoRow.innerHTML = `<span>${escapeHtml(g.banco)}</span><span class="check">${parcial ? ICONE_INDETERMINADO : ICONE_CHECK}</span>`
    grupoRow.onclick = () => toggleGrupoContaFiltro(prefixo, g.banco)
    lista.appendChild(grupoRow)

    contasVisiveis.forEach(c => {
      const row = document.createElement("div")
      row.className = "filtro-item-linha filtro-item-indentado" + (selecionadas.has(c.id) ? " selecionado" : "")
      row.innerHTML = `<span>${escapeHtml(c.nome)}</span><span class="check">${ICONE_CHECK}</span>`
      row.onclick = () => toggleContaFiltro(prefixo, c.id)
      lista.appendChild(row)
    })
  })
  atualizarBtnFiltroConta(prefixo)
}

function todasContasIds() { return estadoGlobal.contasCache.map(c => c.id) }

function colapsarContasSeTudoSelecionado(prefixo) {
  const total = todasContasIds().length
  if (total > 0 && estadoGlobal.contasSelecionadas[prefixo].size === total) estadoGlobal.contasSelecionadas[prefixo].clear()
}

function toggleGrupoContaFiltro(prefixo, banco) {
  const idsGrupo = estadoGlobal.contasCache.filter(c => bancoOuSemBanco(c.banco) === banco).map(c => c.id)
  const selecionadas = estadoGlobal.contasSelecionadas[prefixo]
  const todasJaSelecionadas = idsGrupo.every(id => selecionadas.has(id))
  if (todasJaSelecionadas) idsGrupo.forEach(id => selecionadas.delete(id))
  else idsGrupo.forEach(id => selecionadas.add(id))
  colapsarContasSeTudoSelecionado(prefixo)
  renderizarFiltroConta(prefixo)
  aoMudarFiltroConta(prefixo)
}

function toggleContaFiltro(prefixo, contaId) {
  const selecionadas = estadoGlobal.contasSelecionadas[prefixo]
  if (selecionadas.has(contaId)) selecionadas.delete(contaId)
  else selecionadas.add(contaId)
  colapsarContasSeTudoSelecionado(prefixo)
  renderizarFiltroConta(prefixo)
  aoMudarFiltroConta(prefixo)
}

export function selecionarTodasContasFiltro(prefixo) {
  estadoGlobal.contasSelecionadas[prefixo].clear()
  renderizarFiltroConta(prefixo)
  fecharFiltroConta(prefixo)
  aoMudarFiltroConta(prefixo)
}

function aoMudarFiltroConta(prefixo) {
  if (prefixo === "ct") carregarContas()
  else if (prefixo === "an") carregarAnalise()
  else carregarMovimentos()
}

function nomeContaUnica(prefixo) {
  const id = [...estadoGlobal.contasSelecionadas[prefixo]][0]
  const c = estadoGlobal.contasCache.find(c => c.id === id)
  return c ? c.nome : t("modal_movimento.conta")
}

function atualizarBtnFiltroConta(prefixo) {
  const n = estadoGlobal.contasSelecionadas[prefixo].size
  const label = document.getElementById(prefixo + "-filtro-conta-label")
  const badge = document.getElementById(prefixo + "-filtro-conta-badge")
  if (n > 0) {
    label.textContent = n === 1 ? nomeContaUnica(prefixo) : t("contas.filtro.contas_label")
    if (n > 1) { badge.textContent = n; badge.style.display = "inline-flex" } else badge.style.display = "none"
  } else {
    label.textContent = t("contas.filtro.todas")
    badge.style.display = "none"
  }
}

// ═══════════════════════════════════════════════════════════
// FILTRO DE CATEGORIAS (ANÁLISE)
// ═══════════════════════════════════════════════════════════
// Abre o menu de ações flutuante (usado por contas/reconciliações/movimentos aqui, e por
// grupos/categorias em perfil.js) — antes eram 5 cópias quase idênticas, cada uma com o
// mesmo cálculo de posicionamento; só o conteúdo dos botões e a chave em `dataset` mudavam
// de caso para caso. `chaveDataset` identifica de quem é o menu aberto (para saber se um
// segundo clique no mesmo botão deve fechar em vez de reabrir); `botoesHtml` já vem pronto
// de quem chama, porque os botões variam a sério (mover/editar/eliminar, condicionais a
// protegida/primeiro/último).
export function abrirMenuFlutuante(event, chaveDataset, id, botoesHtml) {
  const menu = document.getElementById("menu-acoes-flutuante")
  const jaAbertoParaEsta = menu.style.display !== "none" && menu.dataset[chaveDataset] === String(id)
  fecharMenusAcoes()
  if (jaAbertoParaEsta) return
  menu.innerHTML = botoesHtml
  const rect = event.currentTarget.getBoundingClientRect()
  menu.style.display = "flex"
  menu.style.left = "auto"
  menu.style.right = (window.innerWidth - rect.right) + "px"
  menu.style.bottom = (window.innerHeight - rect.top + 4) + "px"
  menu.style.top = "auto"
  menu.dataset[chaveDataset] = String(id)
}
export function toggleMenuAcoesConta(event, id) {
  abrirMenuFlutuante(event, "contaId", id, `
    <button onclick="fecharMenusAcoes(); abrirModalAjusteSaldo('${id}')">${t("contas.menu.reconciliacoes")}</button>
    <button onclick="fecharMenusAcoes(); abrirEditarConta('${id}')">${t("generico.editar")}</button>
    <button class="perigo" onclick="fecharMenusAcoes(); eliminarConta('${id}')">${t("generico.eliminar")}</button>
  `)
}
export function toggleMenuAcoesReconciliacao(event, id, data, valor) {
  abrirMenuFlutuante(event, "reconcId", id, `
    <button onclick="fecharMenusAcoes(); mostrarFormReconciliacao(${id},'${data}',${valor})">${t("generico.editar")}</button>
    <button class="perigo" onclick="fecharMenusAcoes(); eliminarReconciliacao(${id})">${t("generico.eliminar")}</button>
  `)
}
export function toggleMenuAcoesMovimento(event, id) {
  abrirMenuFlutuante(event, "movId", id, `
    <button onclick="fecharMenusAcoes(); abrirEditarMovimento('${id}')">${t("generico.editar")}</button>
    <button class="perigo" onclick="fecharMenusAcoes(); eliminarMovimento('${id}')">${t("generico.eliminar")}</button>
  `)
}
function toggleAjudaIcone(icone) {
  const jaAberto = document.querySelector(".balao-ajuda")?.dataset.para === icone.id
  fecharBalaoAjuda()
  if (jaAberto) return
  const balao = document.createElement("div")
  balao.className = "balao-ajuda"
  balao.dataset.para = icone.id
  balao.textContent = icone.dataset.ajuda
  document.body.appendChild(balao)
  const rect = icone.getBoundingClientRect()
  const larguraBalao = 240
  balao.style.left = Math.max(8, Math.min(rect.left, window.innerWidth - larguraBalao - 8)) + "px"
  balao.style.top = (rect.bottom + 6) + "px"
}
function fecharBalaoAjuda() {
  document.querySelectorAll(".balao-ajuda").forEach(b => b.remove())
}
document.addEventListener("click", (e) => {
  const icone = e.target.closest(".icone-protegida")
  if (icone) { toggleAjudaIcone(icone); return }
  if (!e.target.closest(".balao-ajuda")) fecharBalaoAjuda()
})
document.querySelector("main").addEventListener("scroll", () => fecharBalaoAjuda(), { passive: true, capture: true })
document.getElementById("reconc-table-wrap").addEventListener("scroll", atualizarSombraScrollReconciliacoes, { passive: true })
export function fecharMenusAcoes() {
  const menu = document.getElementById("menu-acoes-flutuante")
  if (menu) { menu.style.display = "none"; menu.dataset.contaId = "" }
}
document.addEventListener("click", (e) => {
  if (!e.target.closest(".menu-acoes-lista") && !e.target.closest("[onclick*='toggleMenuAcoesConta']") && !e.target.closest("[onclick*='toggleMenuAcoesReconciliacao']") && !e.target.closest("[onclick*='toggleMenuAcoesMovimento']") && !e.target.closest("[onclick*='toggleMenuAcoesGrupo']") && !e.target.closest("[onclick*='toggleMenuAcoesCategoria']")) fecharMenusAcoes()
})
document.querySelector("main").addEventListener("scroll", () => fecharMenusAcoes(), { passive: true, capture: true })
export function fecharTodosOsFiltros() {
  fecharCalendarioSimples()
  fecharCalendarioRange()
  fecharFiltroCat()
  fecharOrdenar("mov")
  fecharOrdenar("ct")
  fecharOrdenar("an-recorrentes")
  fecharFiltroCategoriaMov()
  fecharFiltroConta("ct")
  fecharFiltroConta("an")
  fecharFiltroConta("mov")
  fecharSeletorContaForm()
  fecharSeletorCategoriaMovForm()
  fecharSeletorTipoMovForm()
  fecharSeletorMoeda()
  fecharMenuAvatar()
}

export function toggleFiltroCat(e) {
  e.stopPropagation()
  const painel = document.getElementById("filtro-cat-panel")
  const estavaAberto = estadoGlobal.filtroCatAberto
  fecharTodosOsFiltros()
  estadoGlobal.filtroCatAberto = !estavaAberto
  painel.classList.toggle("aberto", estadoGlobal.filtroCatAberto)
  document.getElementById("filtro-cat-btn").classList.toggle("ativo", estadoGlobal.filtroCatAberto)
  if (estadoGlobal.filtroCatAberto) painel.scrollTop = 0
}

export function fecharFiltroCat() {
  estadoGlobal.filtroCatAberto = false
  document.getElementById("filtro-cat-panel").classList.remove("aberto")
  document.getElementById("filtro-cat-btn").classList.remove("ativo")
}

export function todasCategoriasIdsAnalise() {
  return estadoGlobal.arvoreAnaliseCache.flatMap(g => g.categorias.map(c => c.id))
}

function nomeCategoriaAnaliseUnica() {
  const id = [...estadoGlobal.categoriasSelecionadas][0]
  for (const g of estadoGlobal.arvoreAnaliseCache) {
    const c = g.categorias.find(c => c.id === id)
    if (c) return nomeCategoria(c.nome, c.slug)
  }
  return t("movimentos.coluna.categoria")
}

function atualizarBtnFiltroCat() {
  const n = estadoGlobal.categoriasSelecionadas.size
  const badge = document.getElementById("filtro-cat-badge")
  const label = document.getElementById("filtro-cat-label")
  if (n > 0) {
    label.textContent = n === 1 ? nomeCategoriaAnaliseUnica() : t("movimentos.filtro.categorias_label")
    if (n > 1) { badge.textContent = n; badge.style.display = "inline-flex" } else badge.style.display = "none"
  } else {
    label.textContent = t("contas.filtro.todas")
    badge.style.display = "none"
  }
}

function todasCategoriaIdsEsfera(ehRecebimento) {
  return estadoGlobal.arvoreAnaliseCache.filter(g => g.eh_recebimento === ehRecebimento).flatMap(g => g.categorias.map(c => c.id))
}

function construirArvoreFiltrada(termo) {
  const termoBusca = (termo || "").trim().toLowerCase()
  const esferas = [{ label: t("generico.entradas"), eh: true }, { label: t("generico.saidas"), eh: false }]
  const resultado = []
  esferas.forEach(esfera => {
    const esferaBate = !termoBusca || esfera.label.toLowerCase().includes(termoBusca)
    const grupos = []
    estadoGlobal.arvoreAnaliseCache.filter(g => g.eh_recebimento === esfera.eh).forEach(g => {
      const nomeGrupo = nomeCategoria(g.nome, g.slug)
      const grupoBate = esferaBate || nomeGrupo.toLowerCase().includes(termoBusca)
      const categorias = grupoBate ? g.categorias : g.categorias.filter(c => nomeCategoria(c.nome, c.slug).toLowerCase().includes(termoBusca))
      if (!termoBusca || grupoBate || categorias.length > 0) grupos.push({ ...g, categorias })
    })
    if (!termoBusca || esferaBate || grupos.length > 0) resultado.push({ ...esfera, grupos })
  })
  return resultado
}

function getSetCategoriaFiltro(espaco) {
  return espaco === "an" ? estadoGlobal.categoriasSelecionadas : estadoGlobal.categoriasMovSelecionadas
}

export function renderizarFiltroCategoriaEspaco(espaco) {
  const listaId = espaco === "an" ? "filtro-cat-lista" : "mov-filtro-categoria-lista"
  const pesquisaId = espaco === "an" ? "filtro-cat-pesquisa" : "mov-filtro-categoria-pesquisa"
  const lista = document.getElementById(listaId)
  if (!lista) return
  const selecionadas = getSetCategoriaFiltro(espaco)
  const inputPesquisa = document.getElementById(pesquisaId)
  const termo = inputPesquisa ? inputPesquisa.value : ""

  lista.innerHTML = ""
  const arvore = construirArvoreFiltrada(termo)
  arvore.forEach((esfera, indiceEsfera) => {
    const idsEsfera = todasCategoriaIdsEsfera(esfera.eh)
    const nSelEsfera = idsEsfera.filter(id => selecionadas.has(id)).length
    const esferaCompleta = idsEsfera.length > 0 && nSelEsfera === idsEsfera.length
    const esferaParcial = nSelEsfera > 0 && !esferaCompleta

    const esferaRow = document.createElement("div")
    esferaRow.className = "filtro-item-linha filtro-esfera-linha" + (indiceEsfera > 0 ? " nova-esfera" : "") + (esferaCompleta ? " selecionado" : esferaParcial ? " indeterminado" : "")
    esferaRow.innerHTML = `<span>${esfera.label}</span><span class="check">${esferaParcial ? ICONE_INDETERMINADO : ICONE_CHECK}</span>`
    esferaRow.onclick = () => toggleEsferaCategoriaFiltro(espaco, esfera.eh)
    lista.appendChild(esferaRow)

    esfera.grupos.forEach(gFiltrado => {
      const gOriginal = estadoGlobal.arvoreAnaliseCache.find(x => x.id === gFiltrado.id)
      const idsGrupo = gOriginal.categorias.map(c => c.id)
      const nSelGrupo = idsGrupo.filter(id => selecionadas.has(id)).length
      const grupoCompleto = idsGrupo.length > 0 && nSelGrupo === idsGrupo.length
      const grupoParcial = nSelGrupo > 0 && !grupoCompleto

      const grupoRow = document.createElement("div")
      grupoRow.className = "filtro-item-linha filtro-grupo-linha" + (grupoCompleto ? " selecionado" : grupoParcial ? " indeterminado" : "")
      grupoRow.innerHTML = `<span>${escapeHtml(nomeCategoria(gFiltrado.nome, gFiltrado.slug))}</span><span class="check">${grupoParcial ? ICONE_INDETERMINADO : ICONE_CHECK}</span>`
      grupoRow.onclick = () => toggleGrupoCategoriaFiltroArvore(espaco, gFiltrado.id)
      lista.appendChild(grupoRow)

      gFiltrado.categorias.forEach(c => {
        const catRow = document.createElement("div")
        catRow.className = "filtro-item-linha filtro-item-indentado" + (selecionadas.has(c.id) ? " selecionado" : "")
        catRow.innerHTML = `<span>${escapeHtml(nomeCategoria(c.nome, c.slug))}</span><span class="check">${ICONE_CHECK}</span>`
        catRow.onclick = () => toggleCategoriaFiltroArvore(espaco, c.id)
        lista.appendChild(catRow)
      })
    })
  })

  if (espaco === "an") atualizarBtnFiltroCat()
  else atualizarBtnFiltroCategoriaMov()
}

function colapsarCategoriaFiltroSeTudoSelecionado(espaco) {
  const selecionadas = getSetCategoriaFiltro(espaco)
  const total = todasCategoriasIdsAnalise().length
  if (total > 0 && selecionadas.size === total) selecionadas.clear()
}

function toggleEsferaCategoriaFiltro(espaco, ehRecebimento) {
  const selecionadas = getSetCategoriaFiltro(espaco)
  const ids = todasCategoriaIdsEsfera(ehRecebimento)
  const todasJaSelecionadas = ids.every(id => selecionadas.has(id))
  if (todasJaSelecionadas) ids.forEach(id => selecionadas.delete(id))
  else ids.forEach(id => selecionadas.add(id))
  colapsarCategoriaFiltroSeTudoSelecionado(espaco)
  renderizarFiltroCategoriaEspaco(espaco)
  if (espaco === "an") carregarAnalise(); else carregarMovimentos()
}

function toggleGrupoCategoriaFiltroArvore(espaco, grupoId) {
  const grupo = estadoGlobal.arvoreAnaliseCache.find(g => g.id === grupoId)
  if (!grupo) return
  const selecionadas = getSetCategoriaFiltro(espaco)
  const ids = grupo.categorias.map(c => c.id)
  const todasJaSelecionadas = ids.every(id => selecionadas.has(id))
  if (todasJaSelecionadas) ids.forEach(id => selecionadas.delete(id))
  else ids.forEach(id => selecionadas.add(id))
  colapsarCategoriaFiltroSeTudoSelecionado(espaco)
  renderizarFiltroCategoriaEspaco(espaco)
  if (espaco === "an") carregarAnalise(); else carregarMovimentos()
}

function toggleCategoriaFiltroArvore(espaco, categoriaId) {
  const selecionadas = getSetCategoriaFiltro(espaco)
  if (selecionadas.has(categoriaId)) selecionadas.delete(categoriaId)
  else selecionadas.add(categoriaId)
  colapsarCategoriaFiltroSeTudoSelecionado(espaco)
  renderizarFiltroCategoriaEspaco(espaco)
  if (espaco === "an") carregarAnalise(); else carregarMovimentos()
}

export function selecionarTodasCategoriaFiltroArvore(espaco) {
  getSetCategoriaFiltro(espaco).clear()
  renderizarFiltroCategoriaEspaco(espaco)
  if (espaco === "an") { atualizarBtnFiltroCat(); fecharFiltroCat(); carregarAnalise() }
  else { atualizarBtnFiltroCategoriaMov(); fecharFiltroCategoriaMov(); carregarMovimentos() }
}

// ═══════════════════════════════════════════════════════════
// FILTRO DE CATEGORIAS (Movimentos)
// ═══════════════════════════════════════════════════════════
export function toggleFiltroCategoriaMov(e) {
  e.stopPropagation()
  const painel = document.getElementById("mov-filtro-categoria-panel")
  const estavaAberto = painel.classList.contains("aberto")
  fecharTodosOsFiltros()
  const btn = document.getElementById("mov-filtro-categoria-btn")
  const abrir = !estavaAberto
  painel.classList.toggle("aberto", abrir)
  btn.classList.toggle("ativo", abrir)
  if (abrir) painel.scrollTop = 0
}
export function fecharFiltroCategoriaMov() {
  document.getElementById("mov-filtro-categoria-panel").classList.remove("aberto")
  document.getElementById("mov-filtro-categoria-btn").classList.remove("ativo")
}

function nomeCategoriaMovUnica() {
  const id = [...estadoGlobal.categoriasMovSelecionadas][0]
  for (const g of estadoGlobal.arvoreAnaliseCache) {
    const c = g.categorias.find(c => c.id === id)
    if (c) return nomeCategoria(c.nome, c.slug)
  }
  return t("movimentos.coluna.categoria")
}

function atualizarBtnFiltroCategoriaMov() {
  const n = estadoGlobal.categoriasMovSelecionadas.size
  const label = document.getElementById("mov-filtro-categoria-label")
  const badge = document.getElementById("mov-filtro-categoria-badge")
  if (n > 0) {
    label.textContent = n === 1 ? nomeCategoriaMovUnica() : t("movimentos.filtro.categorias_label")
    if (n > 1) { badge.textContent = n; badge.style.display = "inline-flex" } else badge.style.display = "none"
  } else {
    label.textContent = t("contas.filtro.todas")
    badge.style.display = "none"
  }
}

// ═══════════════════════════════════════════════════════════
