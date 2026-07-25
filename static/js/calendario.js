import { carregarAnalise } from './analise.js'
import { atualizarSaldoAtualReconciliacao, carregarContas } from './contas.js'
import { estadoGlobal } from './estado.js'
import { fecharMenusAcoes, fecharTodosOsFiltros } from './filtros.js'
import { nomesDiasAbrev, nomesMesesCompletos, t } from './i18n.js'
import { carregarMovimentos } from './movimentos.js'
import { fmtData, isoDateStr } from './utils.js'

// CALENDÁRIOS (LITEPICKER)
// ═══════════════════════════════════════════════════════════
export function primeiroDiaMes()         { const h = new Date(); return new Date(h.getFullYear(), h.getMonth(), 1) }
function primeiroDiaAno()         { const h = new Date(); return new Date(h.getFullYear(), 0, 1) }
function menosDias(n)             { const h = new Date(); h.setDate(h.getDate() - n); return h }
function primeiroDiaMesAnterior() { const h = new Date(); return new Date(h.getFullYear(), h.getMonth() - 1, 1) }
function ultimoDiaMesAnterior()   { const h = new Date(); return new Date(h.getFullYear(), h.getMonth(), 0) }
function primeiroDiaAnoAnterior() { const h = new Date(); return new Date(h.getFullYear() - 1, 0, 1) }
function ultimoDiaAnoAnterior()   { const h = new Date(); return new Date(h.getFullYear() - 1, 11, 31) }


export function iniciarPickerContas() {
  definirIntervaloCalendarioRange("ct-periodo-btn", estadoGlobal.ctDataDe, estadoGlobal.ctDataAte)
  document.getElementById("ct-periodo-btn-wrapper").onclick = () =>
    abrirCalendarioRange("ct-periodo-btn", estadoGlobal.ctDataDe, estadoGlobal.ctDataAte, { maxDays: 365, aoAplicar: (d1, d2) => { estadoGlobal.ctDataDe = d1; estadoGlobal.ctDataAte = d2; carregarContas() } })

}
export function iniciarPickerAnalise() {
  definirIntervaloCalendarioRange("an-periodo", estadoGlobal.anDataDe, estadoGlobal.anDataAte)
  document.getElementById("an-periodo-wrapper").onclick = () =>
    abrirCalendarioRange("an-periodo", estadoGlobal.anDataDe, estadoGlobal.anDataAte, { maxDays: 365, aoAplicar: (d1, d2) => { estadoGlobal.anDataDe = d1; estadoGlobal.anDataAte = d2; carregarAnalise() } })

}
export function iniciarPickerMovimentos() {
  definirIntervaloCalendarioRange("mov-periodo", estadoGlobal.movDataDe, estadoGlobal.movDataAte)
  document.getElementById("mov-periodo-wrapper").onclick = () =>
    abrirCalendarioRange("mov-periodo", estadoGlobal.movDataDe, estadoGlobal.movDataAte, { maxDays: 365, aoAplicar: (d1, d2) => { estadoGlobal.movDataDe = d1; estadoGlobal.movDataAte = d2; carregarMovimentos() } })

}
export function iniciarPickerMovData() {
  document.getElementById("mov-data-wrapper").onclick = () => abrirCalendarioSimples("mov-data")
}
export function iniciarPickerReconciliacao() {
  document.getElementById("reconc-data-wrapper").onclick = () => {
    if (document.getElementById("reconc-data").disabled) return
    abrirCalendarioSimples("reconc-data", { maxDate: isoDateStr(new Date()), aoSelecionar: atualizarSaldoAtualReconciliacao })
  }
}
export let calendarioEstado = null   // { inputId, ano, mes, maxDate, minDate }

// Peças partilhadas entre o calendário de data única e o de intervalo — o resto (a lógica
// de selecção em si, células da grelha) fica em cada renderizarCalendarioX porque a
// diferença aí é real (um dia seleccionado vs. um intervalo com início/fim/presets), não
// só duplicação por preguiça.
function diasDoMes(ano, mes) {
  const diaSemanaInicio = (new Date(ano, mes, 1).getDay() + 6) % 7
  const diasNoMes = new Date(ano, mes + 1, 0).getDate()
  return { diaSemanaInicio, diasNoMes }
}
function opcoesMesEAno(mesSelecionado, anoSelecionado) {
  const opcoesMes = nomesMesesCompletos().map((nome, i) => `<option value="${i}" ${i === mesSelecionado ? "selected" : ""}>${nome}</option>`).join("")
  const anoAtual = new Date().getFullYear()
  let opcoesAno = ""
  for (let a = anoAtual; a >= 1970; a--) opcoesAno += `<option value="${a}" ${a === anoSelecionado ? "selected" : ""}>${a}</option>`
  return { opcoesMes, opcoesAno }
}
function cabecalhoCalendarioHtml({ tipo, mes, ano, podeRecuar = true, podeAvancar = true }) {
  const { opcoesMes, opcoesAno } = opcoesMesEAno(mes, ano)
  const diasSemana = nomesDiasAbrev().map(d => `<span>${d}</span>`).join("")
  return `
    <div class="cal-header">
      <button type="button" class="cal-nav" onclick="navegarCalendario('${tipo}', -1)" ${podeRecuar ? "" : "disabled"} aria-label="${t("calendario.mes_anterior")}">‹</button>
      <span class="cal-titulo-selects">
        <select class="cal-select" onchange="mudarMesCalendario('${tipo}', this.value)" aria-label="${t("calendario.mes_aria")}">${opcoesMes}</select>
        <select class="cal-select" onchange="mudarAnoCalendario('${tipo}', this.value)" aria-label="${t("calendario.ano_aria")}">${opcoesAno}</select>
      </span>
      <button type="button" class="cal-nav" onclick="navegarCalendario('${tipo}', 1)" ${podeAvancar ? "" : "disabled"} aria-label="${t("calendario.mes_seguinte")}">›</button>
    </div>
    <div class="cal-semana">${diasSemana}</div>
  `
}

function valorIsoDoCampo(inputId) {
  const campoIso = document.getElementById(inputId + "-iso")
  return campoIso ? campoIso.value : document.getElementById(inputId).value
}
function abrirCalendarioSimples(inputId, opcoes = {}) {
  if (calendarioEstado && calendarioEstado.inputId === inputId) { fecharCalendarioSimples(); return }
  fecharTodosOsFiltros(); fecharMenusAcoes()
  const input = document.getElementById(inputId)
  const valorIso = valorIsoDoCampo(inputId)
  const valorAtual = valorIso ? new Date(valorIso + "T00:00:00") : new Date()
  calendarioEstado = {
    inputId,
    ano: valorAtual.getFullYear(),
    mes: valorAtual.getMonth(),
    maxDate: opcoes.maxDate || null,
    minDate: opcoes.minDate || null,
    aoSelecionar: opcoes.aoSelecionar || null,
  }
  renderizarCalendarioSimples()
  const panel = document.getElementById("calendario-panel")
  panel.style.display = "block"
  const rect = input.getBoundingClientRect()
  panel.style.left = Math.min(rect.left, window.innerWidth - 282) + "px"
  reposicionarCalendario("simples")
}
export function fecharCalendarioSimples() {
  document.getElementById("calendario-panel").style.display = "none"
  calendarioEstado = null
}
function renderizarCalendarioSimples() {
  if (!calendarioEstado) return
  const { ano, mes, maxDate, minDate } = calendarioEstado
  const diaSelecionado = valorIsoDoCampo(calendarioEstado.inputId) || null
  const { diaSemanaInicio, diasNoMes } = diasDoMes(ano, mes)
  const hoje = isoDateStr(new Date())

  let celulas = ""
  for (let i = 0; i < diaSemanaInicio; i++) celulas += `<div class="cal-dia cal-vazio"></div>`
  for (let d = 1; d <= diasNoMes; d++) {
    const dataIso = `${ano}-${String(mes+1).padStart(2,"0")}-${String(d).padStart(2,"0")}`
    const desabilitado = (maxDate && dataIso > maxDate) || (minDate && dataIso < minDate)
    const classes = ["cal-dia"]
    if (dataIso === diaSelecionado) classes.push("selecionado")
    if (dataIso === hoje) classes.push("hoje")
    if (desabilitado) classes.push("desabilitado")
    celulas += `<div class="${classes.join(" ")}" ${desabilitado ? "" : `onclick="selecionarDiaCalendarioSimples('${dataIso}')"`}>${d}</div>`
  }

  const mesSeguinte = new Date(ano, mes + 1, 1)
  const podeAvancar = !maxDate || isoDateStr(mesSeguinte) <= maxDate
  const mesAnterior = new Date(ano, mes, 0)
  const podeRecuar = !minDate || isoDateStr(new Date(ano, mes, 1)) > minDate || isoDateStr(mesAnterior) >= minDate

  document.getElementById("calendario-panel").innerHTML = `
    ${cabecalhoCalendarioHtml({ tipo: "simples", mes, ano, podeRecuar, podeAvancar })}
    <div class="cal-grelha">${celulas}</div>
  `
}
export function selecionarDiaCalendarioSimples(dataIso) {
  const input = document.getElementById(calendarioEstado.inputId)
  const callback = calendarioEstado.aoSelecionar
  definirDataCalendarioSimples(calendarioEstado.inputId, dataIso)
  input.dispatchEvent(new Event("input", { bubbles: true }))
  fecharCalendarioSimples()
  if (callback) callback()
}
export function definirDataCalendarioSimples(inputId, dataIso) {
  document.getElementById(inputId).value = dataIso ? fmtData(dataIso) : ""
  const campoIso = document.getElementById(inputId + "-iso")
  if (campoIso) campoIso.value = dataIso || ""
}

export let calendarioRangeEstado = null   // { inputId, ano, mes, dataInicio, dataFim, maxDays, aoAplicar }

function nomesPresetsRange() {
  return {
    [t("calendario.preset.este_mes")]:    [primeiroDiaMes(), new Date()],
    [t("calendario.preset.mes_passado")]: [primeiroDiaMesAnterior(), ultimoDiaMesAnterior()],
    [t("calendario.preset.30_dias")]:     [menosDias(30), new Date()],
    [t("calendario.preset.este_ano")]:    [primeiroDiaAno(), new Date()],
    [t("calendario.preset.ano_passado")]: [primeiroDiaAnoAnterior(), ultimoDiaAnoAnterior()],
    [t("calendario.preset.365_dias")]:    [menosDias(365), new Date()],
  }
}
function abrirCalendarioRange(inputId, dataDeAtual, dataAteAtual, opcoes = {}) {
  if (calendarioRangeEstado && calendarioRangeEstado.inputId === inputId) { fecharCalendarioRange(); return }
  fecharTodosOsFiltros(); fecharMenusAcoes(); fecharCalendarioSimples()
  const input = document.getElementById(inputId)
  const refData = dataDeAtual ? new Date(dataDeAtual + "T00:00:00") : new Date()
  calendarioRangeEstado = {
    inputId,
    ano: refData.getFullYear(),
    mes: refData.getMonth(),
    dataInicio: dataDeAtual || null,
    dataFim: dataAteAtual || null,
    maxDays: opcoes.maxDays || null,
    aoAplicar: opcoes.aoAplicar || null,
  }
  renderizarCalendarioRange()
  const panel = document.getElementById("calendario-range-panel")
  panel.style.display = "flex"
  reposicionarCalendario("range")
}
export function fecharCalendarioRange() {
  document.getElementById("calendario-range-panel").style.display = "none"
  calendarioRangeEstado = null
}
function renderizarCalendarioRange() {
  if (!calendarioRangeEstado) return
  const { ano, mes, dataInicio, dataFim, maxDays } = calendarioRangeEstado
  const { diaSemanaInicio, diasNoMes } = diasDoMes(ano, mes)
  const hoje = isoDateStr(new Date())

  let minSelecionavel = null, maxSelecionavel = null
  if (dataInicio && !dataFim && maxDays) {
    const ini = new Date(dataInicio + "T00:00:00")
    const maxD = new Date(ini); maxD.setDate(maxD.getDate() + maxDays - 1)
    const minD = new Date(ini); minD.setDate(minD.getDate() - maxDays + 1)
    maxSelecionavel = isoDateStr(maxD)
    minSelecionavel = isoDateStr(minD)
  }

  let celulas = ""
  for (let i = 0; i < diaSemanaInicio; i++) celulas += `<div class="cal-dia cal-vazio"></div>`
  for (let d = 1; d <= diasNoMes; d++) {
    const dataIso = `${ano}-${String(mes+1).padStart(2,"0")}-${String(d).padStart(2,"0")}`
    const desabilitado = dataIso > hoje || (minSelecionavel && dataIso < minSelecionavel) || (maxSelecionavel && dataIso > maxSelecionavel)
    const classes = ["cal-dia"]
    if (dataIso === dataInicio) classes.push("selecionado", "range-inicio")
    if (dataIso === dataFim) classes.push("selecionado", "range-fim")
    if (dataInicio && dataFim && dataIso > dataInicio && dataIso < dataFim) classes.push("range-meio")
    if (dataIso === hoje) classes.push("hoje")
    if (desabilitado) classes.push("desabilitado")
    celulas += `<div class="${classes.join(" ")}" ${desabilitado ? "" : `onclick="selecionarDiaCalendarioRange('${dataIso}')"`}>${d}</div>`
  }

  const mesSeguinte = new Date(ano, mes + 1, 1)
  const podeAvancar = isoDateStr(mesSeguinte) <= hoje

  const presets = Object.entries(nomesPresetsRange()).map(([nome, [ini, fim]]) => {
    const ativo = dataInicio === isoDateStr(ini) && dataFim === isoDateStr(fim)
    return `<button type="button" class="cal-range-preset${ativo ? " selecionado" : ""}" onclick="aplicarPresetCalendarioRange('${nome}')">${nome}</button>`
  }).join("")

  const resumo = dataInicio && dataFim ? `${fmtData(dataInicio)} — ${fmtData(dataFim)}` : (dataInicio ? `${fmtData(dataInicio)} — ${t("calendario.escolhe_fim")}` : t("calendario.escolhe_data_inicio"))

  document.getElementById("calendario-range-panel").innerHTML = `
    <div class="cal-range-presets">${presets}</div>
    <div class="cal-range-corpo">
      ${cabecalhoCalendarioHtml({ tipo: "range", mes, ano, podeAvancar })}
      <div class="cal-grelha">${celulas}</div>
      <div class="cal-range-resumo">${resumo}</div>
    </div>
  `
}
export function selecionarDiaCalendarioRange(dataIso) {
  const st = calendarioRangeEstado
  if (!st.dataInicio || st.dataFim) {
    st.dataInicio = dataIso
    st.dataFim = null
  } else if (dataIso < st.dataInicio) {
    st.dataFim = st.dataInicio
    st.dataInicio = dataIso
  } else {
    st.dataFim = dataIso
  }
  renderizarCalendarioRange()
  reposicionarCalendario("range")
  if (st.dataInicio && st.dataFim) aplicarCalendarioRange()
}
export function aplicarPresetCalendarioRange(nome) {
  const [ini, fim] = nomesPresetsRange()[nome]
  calendarioRangeEstado.dataInicio = isoDateStr(ini)
  calendarioRangeEstado.dataFim = isoDateStr(fim)
  aplicarCalendarioRange()
}
function aplicarCalendarioRange() {
  const st = calendarioRangeEstado
  const input = document.getElementById(st.inputId)
  input.value = `${fmtData(st.dataInicio)} — ${fmtData(st.dataFim)}`
  const callback = st.aoAplicar
  fecharCalendarioRange()
  if (callback) callback(st.dataInicio, st.dataFim)
}
function definirIntervaloCalendarioRange(inputId, dataDe, dataAte) {
  document.getElementById(inputId).value = dataDe && dataAte ? `${fmtData(dataDe)} — ${fmtData(dataAte)}` : ""
}

// Navegação de mês/ano e reposicionamento eram 8 funções (4 + 4) quase idênticas entre os
// dois calendários — consolidadas em 4, parametrizadas por tipo ("simples" | "range").
const TIPOS_CALENDARIO = {
  simples: {
    obterEstado: () => calendarioEstado,
    renderizar: renderizarCalendarioSimples,
    painelId: "calendario-panel",
    recalcularLargura: false,   // a posição horizontal é definida uma vez, em abrirCalendarioSimples
  },
  range: {
    obterEstado: () => calendarioRangeEstado,
    renderizar: renderizarCalendarioRange,
    painelId: "calendario-range-panel",
    recalcularLargura: true,   // a largura muda consoante o conteúdo (presets), por isso recalcula-se sempre
  },
}
export function navegarCalendario(tipo, delta) {
  const st = TIPOS_CALENDARIO[tipo].obterEstado()
  st.mes += parseInt(delta)
  if (st.mes < 0) { st.mes = 11; st.ano-- }
  if (st.mes > 11) { st.mes = 0; st.ano++ }
  TIPOS_CALENDARIO[tipo].renderizar()
  reposicionarCalendario(tipo)
}
export function mudarMesCalendario(tipo, mes) {
  TIPOS_CALENDARIO[tipo].obterEstado().mes = parseInt(mes)
  TIPOS_CALENDARIO[tipo].renderizar()
  reposicionarCalendario(tipo)
}
export function mudarAnoCalendario(tipo, ano) {
  TIPOS_CALENDARIO[tipo].obterEstado().ano = parseInt(ano)
  TIPOS_CALENDARIO[tipo].renderizar()
  reposicionarCalendario(tipo)
}
function reposicionarCalendario(tipo) {
  const cfg = TIPOS_CALENDARIO[tipo]
  const input = document.getElementById(cfg.obterEstado().inputId)
  const panel = document.getElementById(cfg.painelId)
  const rect = input.getBoundingClientRect()
  if (cfg.recalcularLargura) {
    const larguraPainel = panel.offsetWidth
    panel.style.left = Math.max(8, Math.min(rect.left, window.innerWidth - larguraPainel - 8)) + "px"
  }
  const alturaPainel = panel.offsetHeight
  const espacoAbaixo = window.innerHeight - rect.bottom
  if (espacoAbaixo >= alturaPainel + 8) {
    panel.style.top = (rect.bottom + 4) + "px"
    panel.style.bottom = "auto"
  } else {
    panel.style.top = "auto"
    panel.style.bottom = (window.innerHeight - rect.top + 4) + "px"
  }
}

export function iniciarPickerContaData() {
  document.getElementById("conta-data-wrapper").onclick = () => abrirCalendarioSimples("conta-data", { maxDate: isoDateStr(new Date()) })
}

// ═══════════════════════════════════════════════════════════
