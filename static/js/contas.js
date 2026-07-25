import { definirDataCalendarioSimples } from './calendario.js'
import { ICONE_CHECK, corTema, estadoGlobal, linhaVerticalPlugin } from './estado.js'
import { atualizarVisibilidadeLimparContas, fecharTodosOsFiltros, ligarCampoComSugestoesInline, limparFiltrosContas, opcoesBancos, opcoesTipos, renderizarFiltroConta, toggleMenuAcoesConta, toggleMenuAcoesReconciliacao, trOuTraco } from './filtros.js'
import { t } from './i18n.js'
import { atualizarIconesOrdenacao, renderizarPainelOrdenar } from './ordenacao.js'
import { camposValidos, confirmarAcao, ligarValidacaoFormulario, linhaVazia, linhasEsqueleto, mostrarGraficoOuVazio, mostrarToast } from './ui.js'
import { api, apiDelete, apiPost, apiPut, codigoErro, destruirGrafico, escapeHtml, fecharModal, fmt, fmtData, fmtDiaCompleto, fmtDiaCurto, guardarFiltrosPagina, isoDateStr, mensagemDeErro, moedaPredominante, somarDiasIso } from './utils.js'

// PÁGINA: CONTAS
// ═══════════════════════════════════════════════════════════
export async function carregarContas() {
  document.getElementById("tabela-contas").innerHTML = linhasEsqueleto(6, 3)
  const contasSel = estadoGlobal.contasSelecionadas.ct
  guardarFiltrosPagina("contas", { contas: [...contasSel], dataDe: estadoGlobal.ctDataDe, dataAte: estadoGlobal.ctDataAte })
  atualizarVisibilidadeLimparContas()
  estadoGlobal.contasCache = await api("/contas")
  renderizarFiltroConta("ct")
  const params = new URLSearchParams()
  if (contasSel.size > 0) params.set("conta_id", [...contasSel].join(","))
  if (estadoGlobal.ctDataDe)  params.set("data_de", estadoGlobal.ctDataDe)
  if (estadoGlobal.ctDataAte) params.set("data_ate", estadoGlobal.ctDataAte)
  const qs = params.toString() ? "?" + params.toString() : ""
  const saldoDiario = await api("/stats/saldo-diario" + qs)
  let contasFiltradas = estadoGlobal.contasCache
  if (contasSel.size > 0) contasFiltradas = contasFiltradas.filter(c => contasSel.has(c.id))
  renderizarCardSaldoTotal(contasFiltradas)
  renderizarGraficoSaldo(saldoDiario, moedaPredominante(contasFiltradas))
  estadoGlobal.contasTabelaCache = contasFiltradas
  renderizarTabelaContas()
}

function renderizarCardSaldoTotal(lista) {
  const moeda = moedaPredominante(lista)
  const total = lista.reduce((s, c) => s + c.saldo, 0)
  const classe = total >= 0 ? "positivo" : "negativo"
  document.getElementById("ct-card-total").innerHTML = `<div class="card destaque ${classe}"><h3>${t("contas.saldo_total")}</h3><div class="valor ${classe}">${fmt(total, moeda)}</div><div class="sub">${lista.length} ${t("contas.conta_ou_contas")}</div></div>`
}

function renderizarGraficoSaldo(saldoDiario, moeda) {
  mostrarGraficoOuVazio("grafico-saldo-mensal", saldoDiario.length > 0, t("contas.sem_dados_saldo"), () => {
    destruirGrafico("saldoMensal")
    const corSaldo = saldoDiario.length && saldoDiario[saldoDiario.length - 1].saldo < 0 ? corTema("#c0392b", "#f87171") : corTema("#1a7a4a", "#4ade80")
    const maxTicksX = window.innerWidth < 769 ? 4 : 8
    const passoX = Math.max(1, Math.round(saldoDiario.length / maxTicksX))
    const inicioX = Math.floor(passoX / 2)
    const indicesEtiquetaX = new Set()
    for (let i = inicioX; i < saldoDiario.length; i += passoX) indicesEtiquetaX.add(i)
    estadoGlobal.graficos.saldoMensal = new Chart(document.getElementById("grafico-saldo-mensal"), {
      type: "line",
      plugins: [linhaVerticalPlugin],
      data: { labels: saldoDiario.map(s => fmtDiaCurto(s.data)), datasets: [{ label: "Saldo", data: saldoDiario.map(s => s.saldo), borderColor: corSaldo, backgroundColor: corSaldo + "14", fill: true, tension: 0, pointRadius: 0, pointHoverRadius: 5 }] },
      options: { aspectRatio: window.innerWidth < 769 ? 1.3 : 2, layout: { padding: window.innerWidth < 769 ? { left: 0, right: 0, top: 0, bottom: 0 } : {} }, plugins: { legend: { display: false }, tooltip: { callbacks: { title: ctx => fmtDiaCompleto(saldoDiario[ctx[0].dataIndex].data), label: ctx => ` ${fmt(ctx.raw, moeda)}` } } }, interaction: { mode: 'index', intersect: false }, scales: { x: { offset: false, grid: { display: false }, ticks: { autoSkip: false, callback: function(valor, indice) { return indicesEtiquetaX.has(indice) ? this.getLabelForValue(valor) : null } } }, y: { display: window.innerWidth >= 769, border: { display: false }, ticks: { autoSkip: true, maxTicksLimit: window.innerWidth < 769 ? 4 : 6 } } } }
    })
  })
}
export function ordenarContas(campo) {
  estadoGlobal.ordenacaoContas.campo === campo ? estadoGlobal.ordenacaoContas.direcao *= -1 : (estadoGlobal.ordenacaoContas.campo = campo, estadoGlobal.ordenacaoContas.direcao = 1)
  renderizarTabelaContas()
}
export function renderizarTabelaContas() {
  let lista = [...estadoGlobal.contasTabelaCache]
  renderizarPainelOrdenar("ct")
  const { campo, direcao } = estadoGlobal.ordenacaoContas
  if (campo) lista.sort((a, b) => {
    let va = a[campo], vb = b[campo]
    if (campo === "banco" || campo === "tipo") { va = (va && va.trim()) ? va : "\uFFFF"; vb = (vb && vb.trim()) ? vb : "\uFFFF" }
    if (typeof va === "string") { va = va.toLowerCase(); vb = vb.toLowerCase() }
    return va < vb ? -direcao : va > vb ? direcao : 0
  })
  atualizarIconesOrdenacao("cabecalho-contas", estadoGlobal.ordenacaoContas)
  const tb = document.getElementById("tabela-contas")
  if (lista.length === 0) {
    tb.innerHTML = estadoGlobal.contasSelecionadas.ct.size > 0
      ? linhaVazia(7, null, t("contas.vazio.nenhuma_encontrada"), `<button class="btn-sm" onclick="limparFiltrosContas()">${t("contas.vazio.limpar_filtro")}</button>`)
      : linhaVazia(7, null, t("contas.vazio.sem_contas"), `<button class="btn-primary" onclick="abrirModalConta()">${t("contas.adicionar_botao")}</button>`)
    return
  }
  tb.innerHTML = ""
  lista.forEach(c => {
    tb.innerHTML += `<tr class="linha-expandivel" onclick="toggleLinhaExpandida(this)"><td data-label="${t("contas.coluna.nome")}">${escapeHtml(c.nome)}</td><td data-label="${t("contas.coluna.banco")}">${escapeHtml(trOuTraco(c.banco))}</td><td data-label="${t("contas.coluna.tipo")}" class="td-expandido">${escapeHtml(trOuTraco(c.tipo))}</td><td data-label="${t("contas.coluna.iban")}" class="td-expandido">${escapeHtml(trOuTraco(c.iban))}</td><td data-label="${t("contas.coluna.inicio")}" class="td-expandido">${c.inicio}</td><td data-label="${t("contas.coluna.saldo")}" style="text-align:right" class="${c.saldo >= 0 ? 'positivo' : 'negativo'}">${fmt(c.saldo, c.moeda)}</td><td class="td-acoes td-expandido" style="white-space:nowrap">
      <span class="acoes-desktop">
        <button class="btn-sm" onclick="event.stopPropagation(); toggleMenuAcoesConta(event, '${c.id}')" aria-label="${t("contas.acoes.mais_acoes")}">⋮</button>
      </span>
      <span class="acoes-mobile">
        <button class="btn-sm" onclick="event.stopPropagation(); abrirModalAjusteSaldo('${c.id}')">${t("contas.acoes.reconciliacoes")}</button>
        <button class="btn-sm" onclick="event.stopPropagation(); abrirEditarConta('${c.id}')">${t("contas.acoes.editar")}</button>
        <button class="btn-danger" onclick="event.stopPropagation(); eliminarConta('${c.id}')" aria-label="${t("contas.acoes.eliminar")}">✕</button>
      </span>
    </td></tr>`
  })
}
export function toggleLinhaExpandida(tr) { tr.classList.toggle("expandido") }
export function abrirModalConta() {
  document.getElementById("modal-conta-titulo").textContent = t("modal_conta.titulo_adicionar")
  document.getElementById("conta-id").value = ""; document.getElementById("conta-nome").value = ""; document.getElementById("conta-banco").value = ""; document.getElementById("conta-tipo").value = ""; document.getElementById("conta-iban").value = ""
  document.getElementById("conta-moeda").value = ""; document.getElementById("conta-moeda-display").value = ""; renderizarSeletorMoeda(null)
  document.getElementById("conta-saldo").value = ""
  document.getElementById("conta-saldo-campo").style.display = "block"
  document.getElementById("conta-data-campo-adicionar").style.display = "block"
  definirDataCalendarioSimples("conta-data", isoDateStr(new Date()))
  document.getElementById("modal-conta").classList.add("open")
  ligarCampoComSugestoesInline("conta-banco", opcoesBancos); ligarCampoComSugestoesInline("conta-tipo", opcoesTipos)
  ligarValidacaoFormulario(["conta-nome", "conta-moeda-display", "conta-saldo", "conta-data"], "btn-guardar-conta")
}
export async function abrirEditarConta(id) {
  const c = estadoGlobal.contasCache.find(x => x.id === id)
  document.getElementById("modal-conta-titulo").textContent = t("modal_conta.titulo_editar")
  document.getElementById("conta-id").value = c.id
  document.getElementById("conta-nome").value = c.nome
  document.getElementById("conta-banco").value = c.banco || ""
  document.getElementById("conta-tipo").value = c.tipo || ""
  document.getElementById("conta-iban").value = c.iban || ""
  document.getElementById("conta-moeda").value = c.moeda
  const opcaoMoeda = OPCOES_MOEDA.find(o => o.valor === c.moeda)
  document.getElementById("conta-moeda-display").value = opcaoMoeda ? opcaoMoeda.label : (c.moeda || "")
  renderizarSeletorMoeda(c.moeda)
  document.getElementById("conta-saldo-campo").style.display = "block"
  document.getElementById("conta-data-campo-adicionar").style.display = "block"
  document.getElementById("modal-conta").classList.add("open")
  ligarCampoComSugestoesInline("conta-banco", opcoesBancos); ligarCampoComSugestoesInline("conta-tipo", opcoesTipos)
  ligarValidacaoFormulario(["conta-nome", "conta-moeda-display", "conta-saldo", "conta-data"], "btn-guardar-conta")
  document.getElementById("conta-data").value = ""
  document.getElementById("conta-data-iso").value = ""
  document.getElementById("conta-saldo").value = ""
  const inicio = await api("/contas/" + id + "/inicio")
  definirDataCalendarioSimples("conta-data", inicio.data)
  document.getElementById("conta-saldo").value = inicio.saldo_real
}

export async function guardarConta() {
  const id = document.getElementById("conta-id").value
  if (!camposValidos("conta-nome", "conta-moeda-display", "conta-saldo", "conta-data")) return
  const body = { nome: document.getElementById("conta-nome").value, banco: document.getElementById("conta-banco").value, tipo: document.getElementById("conta-tipo").value, iban: document.getElementById("conta-iban").value, moeda: document.getElementById("conta-moeda").value }
  if (id) {
    let r = await apiPut("/contas/" + id, body)
    if (!r.ok) { mostrarToast(mensagemDeErro(await r.json()), "erro"); return }
    const bodyInicio = { data: document.getElementById("conta-data-iso").value, saldo_real: parseFloat(document.getElementById("conta-saldo").value) }
    let r2 = await apiPut("/contas/" + id + "/inicio", bodyInicio)
    if (r2.status === 409) {
      const aviso = await r2.json()
      if (!(await confirmarAcao(mensagemDeErro(aviso), { textoConfirmar: t("contas.confirmar_e_eliminar"), perigo: true }))) return
      r2 = await apiPut("/contas/" + id + "/inicio?confirmar=true", bodyInicio)
    }
    if (!r2.ok) { mostrarToast(mensagemDeErro(await r2.json()), "erro"); return }
  } else {
    body.saldo = parseFloat(document.getElementById("conta-saldo").value)
    body.data = somarDiasIso(document.getElementById("conta-data-iso").value, -1)
    let r = await apiPost("/contas", body)
    if (!r.ok) { mostrarToast(mensagemDeErro(await r.json()), "erro"); return }
  }
  fecharModal(); carregarContas()
}
export async function eliminarConta(id) {
  if (!(await confirmarAcao(t("contas.confirmar_eliminar"), { perigo: true }))) return
  let r = await apiDelete("/contas/" + id)
  if (r.ok) { carregarContas(); return }
  const d = await r.json()
  if (codigoErro(d) !== "CONTA_COM_MOVIMENTOS") { mostrarToast(mensagemDeErro(d), "erro"); return }
  if (!(await confirmarAcao(mensagemDeErro(d), { textoConfirmar: t("contas.eliminar_tudo"), perigo: true }))) return
  r = await apiDelete("/contas/" + id + "?forcar=true")
  if (!r.ok) { mostrarToast(mensagemDeErro(await r.json()), "erro"); return }
  carregarContas()
}

const OPCOES_MOEDA = [
  { valor: "EUR", label: "EUR (€)" },
  { valor: "USD", label: "USD ($)" },
  { valor: "GBP", label: "GBP (£)" },
  { valor: "JPY", label: "JPY (¥)" },
  { valor: "CHF", label: "CHF" },
  { valor: "CAD", label: "CAD (C$)" },
  { valor: "AUD", label: "AUD (A$)" },
  { valor: "CNY", label: "CNY (¥)" },
  { valor: "BRL", label: "BRL (R$)" },
  { valor: "INR", label: "INR (₹)" },
]

export function toggleSeletorMoeda(e) {
  e.stopPropagation()
  const painel = document.getElementById("conta-moeda-panel")
  const estavaAberto = painel.classList.contains("aberto")
  fecharTodosOsFiltros()
  const abrir = !estavaAberto
  painel.classList.toggle("aberto", abrir)
  if (abrir) painel.scrollTop = 0
}
export function fecharSeletorMoeda() {
  document.getElementById("conta-moeda-panel")?.classList.remove("aberto")
}

function renderizarSeletorMoeda(selecionado) {
  const lista = document.getElementById("conta-moeda-lista")
  lista.innerHTML = ""
  OPCOES_MOEDA.forEach(o => {
    const row = document.createElement("div")
    row.className = "filtro-item-linha" + (o.valor === selecionado ? " selecionado" : "")
    row.innerHTML = `<span>${o.label}</span><span class="check">${ICONE_CHECK}</span>`
    row.onclick = () => selecionarMoeda(o.valor)
    lista.appendChild(row)
  })
}

function selecionarMoeda(valor) {
  document.getElementById("conta-moeda").value = valor
  const opcao = OPCOES_MOEDA.find(o => o.valor === valor)
  document.getElementById("conta-moeda-display").value = opcao ? opcao.label : ""
  renderizarSeletorMoeda(valor)
  fecharSeletorMoeda()
  ligarValidacaoFormulario(["conta-nome", "conta-moeda-display", "conta-saldo", "conta-data"], "btn-guardar-conta")
}

// ═══════════════════════════════════════════════════════════
// RECONCILIAÇÕES DE SALDO
// ═══════════════════════════════════════════════════════════
export async function abrirModalAjusteSaldo(id) {
  document.getElementById("modal-conta").classList.remove("open")
  document.getElementById("reconc-conta-id").value = id
  esconderFormReconciliacao()
  await carregarReconciliacoes(id)
  document.getElementById("modal-reconciliacoes").classList.add("open")
  const tabelaWrap = document.querySelector("#modal-reconciliacoes .table-wrap")
  tabelaWrap.scrollTop = 0
  atualizarSombraScrollReconciliacoes()
}
export function fecharModalReconciliacoes() {
  document.getElementById("modal-reconciliacoes").classList.remove("open")
}
async function carregarReconciliacoes(contaId) {
  estadoGlobal.reconciliacoesCache = await api("/contas/" + contaId + "/ajustes-saldo")
  renderizarTabelaReconciliacoes(true)
}
function renderizarTabelaReconciliacoes(comAcoes) {
  const contaId = document.getElementById("reconc-conta-id").value
  const conta = estadoGlobal.contasCache.find(c => c.id === contaId)
  const tb = document.getElementById("tabela-reconciliacoes")
  if (estadoGlobal.reconciliacoesCache.length === 0) {
    tb.innerHTML = linhaVazia(4, null, t("modal_reconc.vazio"))
    return
  }
  tb.innerHTML = ""
  const idEmEdicao = document.getElementById("reconc-id").value
  estadoGlobal.reconciliacoesCache.forEach(a => {
    const emEdicao = idEmEdicao && String(a.id) === idEmEdicao
    tb.innerHTML += `<tr class="${emEdicao ? 'linha-em-edicao' : ''}"><td data-label="${t("modal_reconc.coluna_data")}" style="white-space:nowrap">${fmtData(a.data)}</td><td data-label="${t("modal_reconc.coluna_saldo_anterior")}" style="text-align:right">${fmt(a.saldo_antes, conta?.moeda)}</td><td data-label="${t("modal_reconc.coluna_saldo_reconciliado")}" style="text-align:right">${fmt(a.saldo_real, conta?.moeda)}</td><td class="td-acoes" style="white-space:nowrap"><span style="visibility:${comAcoes ? 'visible' : 'hidden'}">
      <span class="acoes-desktop">
        <button class="btn-sm" onclick="toggleMenuAcoesReconciliacao(event, ${a.id}, '${a.data}', ${a.saldo_real})" aria-label="${t("contas.acoes.mais_acoes")}">⋮</button>
      </span>
      <span class="acoes-mobile">
        <button class="btn-sm" onclick="mostrarFormReconciliacao(${a.id},'${a.data}',${a.saldo_real})">${t("contas.acoes.editar")}</button>
        <button class="btn-danger" onclick="eliminarReconciliacao(${a.id})" aria-label="${t("modal_reconc.eliminar_aria")}">✕</button>
      </span>
    </span></td></tr>`
  })
  atualizarSombraScrollReconciliacoes()
}
export function atualizarSombraScrollReconciliacoes() {
  const el = document.getElementById("reconc-table-wrap")
  if (!el) return
  const temMais = el.scrollHeight - el.scrollTop - el.clientHeight > 4
  el.classList.toggle("tem-scroll-por-ver", temMais)
}
export function mostrarFormReconciliacao(id, data, valor) {
  document.getElementById("reconc-id").value = id || ""
  definirDataCalendarioSimples("reconc-data", data || isoDateStr(new Date()))
  document.getElementById("reconc-data").disabled = !!id
  document.getElementById("reconc-valor").value = valor !== undefined ? valor : ""
  document.getElementById("form-reconciliacao").style.display = "block"
  document.getElementById("btn-add-reconciliacao").style.display = "none"
  renderizarTabelaReconciliacoes(false)
  ligarValidacaoFormulario(["reconc-data", "reconc-valor"], "btn-guardar-reconciliacao")
  if (id) {
    mostrarInfoSaldoContexto("")
  } else {
    atualizarSaldoAtualReconciliacao()
  }
}
function mostrarInfoSaldoContexto(texto) {
  const info = document.getElementById("reconc-saldo-atual-info")
  info.textContent = texto
  info.style.display = texto ? "block" : "none"
}
export async function atualizarSaldoAtualReconciliacao() {
  const aEditar = document.getElementById("reconc-id").value
  if (aEditar) return
  const contaId = document.getElementById("reconc-conta-id").value
  const conta = estadoGlobal.contasCache.find(c => c.id === contaId)
  const data = document.getElementById("reconc-data-iso").value
  if (!data) { mostrarInfoSaldoContexto(""); return }
  try {
    const r = await api("/contas/" + contaId + "/saldo-em-data?data=" + data)
    mostrarInfoSaldoContexto(`${t("modal_reconc.saldo_calculado_prefixo")} ${fmt(r.saldo, conta?.moeda)}.`)
  } catch { mostrarInfoSaldoContexto("") }
}
export function esconderFormReconciliacao() {
  document.getElementById("form-reconciliacao").style.display = "none"
  document.getElementById("btn-add-reconciliacao").style.display = "inline-block"
  document.getElementById("reconc-id").value = ""
  renderizarTabelaReconciliacoes(true)
}
export async function guardarReconciliacao() {
  if (!camposValidos("reconc-data", "reconc-valor")) return
  const id = document.getElementById("reconc-id").value
  const contaId = document.getElementById("reconc-conta-id").value
  const body = { data: document.getElementById("reconc-data-iso").value, saldo_real: parseFloat(document.getElementById("reconc-valor").value) }
  const r = id ? await apiPut("/ajustes-saldo/" + id, body) : await apiPost("/contas/" + contaId + "/ajustes-saldo", body)
  if (!r.ok) { mostrarToast(mensagemDeErro(await r.json()), "erro"); return }
  esconderFormReconciliacao(); await carregarReconciliacoes(contaId); carregarContas()
}
export async function eliminarReconciliacao(id) {
  if (!(await confirmarAcao(t("modal_reconc.confirmar_eliminar"), { perigo: true }))) return
  const contaId = document.getElementById("reconc-conta-id").value
  const r = await apiDelete("/ajustes-saldo/" + id)
  if (!r.ok) { mostrarToast(mensagemDeErro(await r.json()), "erro"); return }
  await carregarReconciliacoes(contaId); carregarContas()
}

// ═══════════════════════════════════════════════════════════
