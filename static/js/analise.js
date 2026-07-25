import { toggleLinhaExpandida } from './contas.js'
import { ICONE_GRAFICO, ICONE_SETA_BAIXO, ICONE_SETA_CIMA, PALETA_VERDE, PALETA_VERMELHA, corTema, estadoGlobal } from './estado.js'
import { atualizarVisibilidadeLimparAnalise, limparFiltrosAnalise, temFiltrosAnaliseAtivos, todasCategoriasIdsAnalise } from './filtros.js'
import { nomeCategoria, t } from './i18n.js'
import { atualizarPosicoesFixas } from './main.js'
import { atualizarIconesOrdenacao, renderizarPainelOrdenar } from './ordenacao.js'
import { linhaVazia, linhasEsqueleto, mostrarGraficoOuVazio } from './ui.js'
import { api, attrJs, destruirGrafico, escapeHtml, fmt, fmtData, fmtMes, guardarFiltrosPagina, moedaPredominante } from './utils.js'

// PÁGINA: ANÁLISE
// ═══════════════════════════════════════════════════════════
export function trocarAbaAnalise(aba) {
  localStorage.setItem("analise_aba", aba)   // ← novo
  document.querySelectorAll(".analise-tab").forEach(el => el.classList.toggle("active", el.dataset.aba === aba))
  document.querySelectorAll(".analise-secao").forEach(el => el.classList.toggle("active", el.id === `analise-secao-${aba}`))
  requestAnimationFrame(() => {
    if (aba === "resumo" && estadoGlobal.analiseCache.mensal !== null) { destruirGrafico("mensal"); renderizarGraficoMensal(estadoGlobal.analiseCache.mensal) }
  })
  setTimeout(() => atualizarPosicoesFixas("page-analise"), 0)
}

function construirParamsAnalise() {
  const contasSel = estadoGlobal.contasSelecionadas.an
  const params = new URLSearchParams()
  if (contasSel.size > 0) params.set("conta_id", [...contasSel].join(","))
  if (estadoGlobal.anDataDe)  params.set("data_de", estadoGlobal.anDataDe)
  if (estadoGlobal.anDataAte) params.set("data_ate", estadoGlobal.anDataAte)
  if (estadoGlobal.categoriasSelecionadas.size > 0) {
    const todasIds = todasCategoriasIdsAnalise()
    const excluidas = todasIds.filter(id => !estadoGlobal.categoriasSelecionadas.has(id))
    if (excluidas.length > 0) params.set("excluir_categorias", excluidas.join(','))
  }
  return params
}

export async function carregarAnalise() {
  fecharDrillDown()
  document.getElementById("tabela-recorrentes").innerHTML = linhasEsqueleto(5, 3)
  document.getElementById("lista-grupos").innerHTML = `<div class="estado-vazio"><div class="subtitulo">${t("generico.a_carregar")}</div></div>`

  const contasSel = estadoGlobal.contasSelecionadas.an

  atualizarVisibilidadeLimparAnalise()
  guardarFiltrosPagina("analise", { contas: [...contasSel], categorias: [...estadoGlobal.categoriasSelecionadas], dataDe: estadoGlobal.anDataDe, dataAte: estadoGlobal.anDataAte })

  let contasConsideradas = estadoGlobal.contasCache
  if (contasSel.size > 0) contasConsideradas = contasConsideradas.filter(c => contasSel.has(c.id))
  estadoGlobal.moedaAnaliseGlobal = moedaPredominante(contasConsideradas)

  const qs = construirParamsAnalise().toString()
  const qsStr = qs ? "?" + qs : ""

  const [mensal, grupos, recorrentes] = await Promise.all([
    api("/stats/mensal" + qsStr),
    api("/stats/grupos" + qsStr),
    api("/stats/recorrentes" + qsStr),
  ])
  estadoGlobal.analiseCache.mensal = mensal

  renderizarResumoAnalise(mensal)
  renderizarGraficoMensal(mensal)
  renderizarRecorrentes(recorrentes)
  estadoGlobal.gruposCache = grupos
  renderizarGrupos()
}

function renderizarResumoAnalise(mensal) {
  const totalIn  = mensal.reduce((s, m) => s + m.entradas, 0)
  const totalOut = mensal.reduce((s, m) => s + m.saidas, 0)
  const pctGasto = totalIn > 0 ? (totalOut / totalIn * 100) : 0
  document.getElementById("summary-mes").innerHTML = `
    <div class="summary-card"><div class="label">${t("generico.entradas")}</div><div class="valor positivo">${fmt(totalIn, estadoGlobal.moedaAnaliseGlobal)}</div></div>
    <div class="summary-card"><div class="label">${t("generico.saidas")}</div><div class="valor negativo">${fmt(totalOut, estadoGlobal.moedaAnaliseGlobal)}</div><div class="sub">${totalIn > 0 ? pctGasto.toFixed(0) + '% ' + t("analise.das_entradas") : ''}</div></div>
    <div class="summary-card"><div class="label">${t("analise.liquido")}</div><div class="valor ${totalIn - totalOut >= 0 ? 'positivo' : 'negativo'}">${fmt(totalIn - totalOut, estadoGlobal.moedaAnaliseGlobal)}</div></div>`
}

function renderizarGraficoMensal(mensal) {
  mostrarGraficoOuVazio("grafico-mensal", mensal.length > 0, t("analise.grafico_vazio"), () => {
    destruirGrafico("mensal")
    estadoGlobal.graficos.mensal = new Chart(document.getElementById("grafico-mensal"), {
      type: "bar",
      data: { labels: mensal.map(m => fmtMes(m.mes)), datasets: [{ label: t("generico.entradas"), data: mensal.map(m => m.entradas), backgroundColor: corTema("#1a7a4a", "#4ade80") }, { label: t("generico.saidas"), data: mensal.map(m => m.saidas), backgroundColor: corTema("#c0392b", "#f87171") }] },
      options: {
        aspectRatio: window.innerWidth < 769 ? 1.3 : 2,
        layout: { padding: window.innerWidth < 769 ? { left: 0, right: 0, top: 0, bottom: 0 } : {} },
        plugins: {
          legend: { labels: { font: { size: 11 } } },
          tooltip: { callbacks: { label: (ctx) => {
            const campo = ctx.datasetIndex === 0 ? 'entradas' : 'saidas'
            let linha = `${ctx.dataset.label}: ${fmt(ctx.raw, estadoGlobal.moedaAnaliseGlobal)}`
            if (ctx.dataIndex > 0) { const anterior = mensal[ctx.dataIndex - 1][campo]; if (anterior > 0) { const v = ((ctx.raw - anterior) / anterior) * 100; linha += ` (${v >= 0 ? '+' : ''}${v.toFixed(0)}% ${t("analise.mes_anterior")})` } }
            return linha
          }}}
        },
        scales: { x: { grid: { display: false }, ticks: { autoSkip: true, maxTicksLimit: window.innerWidth < 769 ? 4 : 8 } }, y: { display: window.innerWidth >= 769, border: { display: false }, ticks: { maxTicksLimit: 6 } } }
      }
    })
  })
}

export function trocarTipo(tipo) {
  estadoGlobal.tipoAtual = tipo
  document.getElementById("btn-tipo-out").classList.toggle("active", tipo === "out")
  document.getElementById("btn-tipo-in").classList.toggle("active", tipo === "in")
  estadoGlobal.gruposExpandidos = false
  atualizarIconeExpandirRecolher()
  fecharDrillDown(); renderizarGrupos()
}

function renderizarGrupos() {
  const filtrados = estadoGlobal.gruposCache.filter(g => estadoGlobal.tipoAtual === "in" ? g.eh_recebimento : !g.eh_recebimento)
  const el = document.getElementById("lista-grupos")
  atualizarIconeExpandirRecolher()
  if (filtrados.length === 0) {
    el.innerHTML = temFiltrosAnaliseAtivos()
      ? `<div class="estado-vazio"><div class="subtitulo">${t("analise.sem_resultados_filtros")}</div><button class="btn-sm" onclick="limparFiltrosAnalise()">${t("movimentos.vazio.limpar_filtros")}</button></div>`
      : `<div class="estado-vazio"><div class="subtitulo">${estadoGlobal.tipoAtual === "in" ? t("analise.sem_entradas_para_analisar") : t("analise.sem_saidas_para_analisar")}</div></div>`
    document.getElementById("total-tipo").textContent = fmt(0, estadoGlobal.moedaAnaliseGlobal)
    document.getElementById("label-tipo").textContent = estadoGlobal.tipoAtual === "in" ? t("generico.entradas") : t("generico.saidas")
    fecharDrillDown(); return
  }
  const totalTipo = filtrados.reduce((s, g) => s + g.total, 0)
  const corBase  = estadoGlobal.tipoAtual === "in" ? corTema("#1a7a4a", "#4ade80") : corTema("#c0392b", "#f87171")
  const corClara = estadoGlobal.tipoAtual === "in" ? "#7fc4a0" : "#e08b7f"
  el.innerHTML = ""
  filtrados.forEach((g, gi) => {
    const pct = totalTipo > 0 ? (g.total / totalTipo * 100) : 0
    const nomeGrupo = nomeCategoria(g.grupo, g.grupo_slug)
    const subcatHtml = g.subcategorias.map(s => {
      const sPct = g.total > 0 ? (s.total / g.total * 100) : 0
      const nomeCat = nomeCategoria(s.categoria, s.categoria_slug)
      return `<div class="sub-item"><span>${escapeHtml(nomeCat)}</span><span style="display:flex;align-items:center;gap:8px"><button class="btn-drilldown" title="${t("analise.ver_evolucao_mensal_de")} ${escapeHtml(nomeCat)}" aria-label="${t("analise.ver_evolucao_mensal_de")} ${escapeHtml(nomeCat)}" onclick="abrirDrillDownCategoria(${s.categoria_id}, ${attrJs(nomeCat)}, ${attrJs(nomeGrupo)})">${ICONE_GRAFICO}</button><span><span class="pct">${sPct.toFixed(1)}%</span>${fmt(s.total, estadoGlobal.moedaAnaliseGlobal)}</span></span></div><div class="sub-barra-fundo"><div class="barra-fill" style="width:${sPct}%;background:${corClara}"></div></div>`
    }).join("")
    el.innerHTML += `<div class="grupo-bar-row"><div class="linha-topo" onclick="toggleGrupo(${gi})" style="cursor:pointer"><span class="nome">${escapeHtml(nomeGrupo)}</span><span style="display:flex;align-items:center;gap:8px"><button class="btn-drilldown" title="${t("analise.ver_evolucao_mensal_de")} ${escapeHtml(nomeGrupo)}" aria-label="${t("analise.ver_evolucao_mensal_de")} ${escapeHtml(nomeGrupo)}" onclick="event.stopPropagation(); abrirDrillDownGrupo(${g.grupo_id}, ${attrJs(nomeGrupo)})">${ICONE_GRAFICO}</button><span class="valores"><span class="pct">${pct.toFixed(1)}%</span><strong>${fmt(g.total, estadoGlobal.moedaAnaliseGlobal)}</strong></span></span></div><div class="barra-fundo"><div class="barra-fill" style="width:${pct}%;background:${corBase}"></div></div><div class="sub-grupo" id="sub-grupo-${gi}">${subcatHtml}</div></div>`
  })
  document.getElementById("total-tipo").textContent = fmt(totalTipo, estadoGlobal.moedaAnaliseGlobal)
  document.getElementById("label-tipo").textContent = estadoGlobal.tipoAtual === "in" ? t("generico.entradas") : t("generico.saidas")
}

export function toggleGrupo(gi) { document.getElementById("sub-grupo-" + gi).classList.toggle("visible") }
export function alternarExpandirTodos() {
  estadoGlobal.gruposExpandidos = !estadoGlobal.gruposExpandidos
  document.querySelectorAll('.sub-grupo').forEach(el => el.classList.toggle('visible', estadoGlobal.gruposExpandidos))
  atualizarIconeExpandirRecolher()
}
export function atualizarIconeExpandirRecolher() {
  const btn = document.getElementById("btn-expandir-recolher")
  btn.innerHTML = estadoGlobal.gruposExpandidos ? ICONE_SETA_CIMA : ICONE_SETA_BAIXO
  btn.setAttribute("aria-label", estadoGlobal.gruposExpandidos ? t("analise.recolher_todos_grupos") : t("analise.expandir_todos_grupos"))
}

// ─── Drill-down ───────────────────────────────────────────
function abrirDrawer(titulo, subtitulo, nomeGrupo, mostrarToggle = false) {
  document.getElementById("drawer-titulo").textContent = titulo
  document.getElementById("drawer-subtitulo").textContent = subtitulo
  const elGrupo = document.getElementById("drawer-titulo-grupo")
  elGrupo.textContent = nomeGrupo || ""
  elGrupo.style.display = nomeGrupo ? "block" : "none"
  document.getElementById("drawer-toggle").style.display = mostrarToggle ? "inline-flex" : "none"
  document.getElementById("drawer-toggle-total").classList.add("active")
  document.getElementById("drawer-toggle-categoria").classList.remove("active")
  document.getElementById("grafico-drilldown").style.display = "none"
  document.getElementById("drilldown-vazio").style.display = "none"
  document.getElementById("modal-drilldown").classList.add("open")
  destruirGrafico("drilldown")
}

export async function abrirDrillDownGrupo(grupoId, nomeGrupo) {
  abrirDrawer(nomeGrupo, t("analise.evolucao_mensal"), null, true)
  const params = construirParamsAnalise()
  params.set("grupo_id", grupoId)
  const dados = await api("/stats/mensal-detalhe?" + params.toString())
  if (!dados.meses || dados.meses.length === 0) { document.getElementById("drilldown-vazio").style.display = "flex"; return }
  estadoGlobal.drilldownAtual = { dados, grupoId }   // ← grupoId adicionado
  renderizarGraficoDrilldownTotal(dados)
}

export function trocarModoDrilldown(modo) {
  if (!estadoGlobal.drilldownAtual) return
  document.getElementById("drawer-toggle-total").classList.toggle("active", modo === "total")
  document.getElementById("drawer-toggle-categoria").classList.toggle("active", modo === "categoria")
  if (modo === "total") renderizarGraficoDrilldownTotal(estadoGlobal.drilldownAtual.dados)
  else renderizarGraficoDrilldownEmpilhado(estadoGlobal.drilldownAtual.dados, estadoGlobal.drilldownAtual.grupoId)   // ← grupoId passado
}

function renderizarGraficoDrilldownTotal(dados) {
  const totaisPorMes = dados.meses.map(m => ({ mes: m.mes, total: dados.categorias.reduce((s, cat) => s + (m.categorias[cat] || 0), 0) }))
  const cor = estadoGlobal.tipoAtual === "in" ? corTema("#1a7a4a", "#4ade80") : corTema("#c0392b", "#f87171")
  destruirGrafico("drilldown")
  document.getElementById("grafico-drilldown").style.display = "block"
  estadoGlobal.graficos.drilldown = new Chart(document.getElementById("grafico-drilldown"), {
    type: "bar",
    data: { labels: totaisPorMes.map(m => fmtMes(m.mes)), datasets: [{ data: totaisPorMes.map(m => m.total), backgroundColor: cor }] },
    options: {
      aspectRatio: window.innerWidth < 769 ? 1.3 : 2,
      layout: { padding: window.innerWidth < 769 ? { left: 0, right: 0, top: 0, bottom: 0 } : {} },
      plugins: { legend: { display: false }, tooltip: { callbacks: { label: ctx => {
        const idx = ctx.dataIndex; let linha = ` ${fmt(ctx.raw, estadoGlobal.moedaAnaliseGlobal)}`
        if (idx > 0) { const ant = totaisPorMes[idx-1].total; if (ant > 0) { const v = ((totaisPorMes[idx].total - ant) / ant) * 100; linha += ` (${v >= 0 ? '+' : ''}${v.toFixed(0)}% ${t("analise.mes_anterior")})` } }
        return linha
      }}}},
      scales: { x: { grid: { display: false }, ticks: { autoSkip: true, maxTicksLimit: window.innerWidth < 769 ? 4 : 8 } }, y: { display: window.innerWidth >= 769, border: { display: false }, ticks: { maxTicksLimit: 6 } } }
    }
  })
}

function renderizarGraficoDrilldownEmpilhado(dados, grupoId) {
  destruirGrafico("drilldown")
  document.getElementById("grafico-drilldown").style.display = "block"
  const grupo = estadoGlobal.arvoreAnaliseCache.find(g => g.id === grupoId)
  const paleta = grupo?.eh_recebimento ? PALETA_VERDE : PALETA_VERMELHA
  const datasets = dados.categorias.map((nomeCat, i) => ({
    label: nomeCategoria(nomeCat, dados.categorias_slugs?.[i]),
    data: dados.meses.map(m => m.categorias[nomeCat] || 0),
    backgroundColor: paleta[i % paleta.length],
  }))
  const totaisPorMes = dados.meses.map(m => dados.categorias.reduce((s, cat) => s + (m.categorias[cat] || 0), 0))   // ← novo
  estadoGlobal.graficos.drilldown = new Chart(document.getElementById("grafico-drilldown"), {
    type: "bar",
    data: { labels: dados.meses.map(m => fmtMes(m.mes)), datasets },
    options: {
      aspectRatio: window.innerWidth < 769 ? 1.3 : 2,
      layout: { padding: window.innerWidth < 769 ? { left: 0, right: 0, top: 0, bottom: 0 } : {} },
      plugins: {
        legend: { position: "bottom", labels: { font: { size: 10 }, boxWidth: 10 } },
        tooltip: { callbacks: { label: ctx => {
          const totalMes = totaisPorMes[ctx.dataIndex]
          const pct = totalMes > 0 ? (ctx.raw / totalMes * 100) : 0
          return ` ${ctx.dataset.label}: ${fmt(ctx.raw, estadoGlobal.moedaAnaliseGlobal)} (${pct.toFixed(0)}% ${t("analise.do_grupo")})`
        }}}
      },
      scales: { x: { grid: { display: false }, stacked: true, ticks: { autoSkip: true, maxTicksLimit: window.innerWidth < 769 ? 4 : 8 } }, y: { stacked: true, display: window.innerWidth >= 769, border: { display: false } } }
    }
  })
}

export async function abrirDrillDownCategoria(categoriaId, nomeCategoriaParam, nomeGrupo) {
  abrirDrawer(nomeCategoriaParam, t("analise.evolucao_mensal"), nomeGrupo, false)
  estadoGlobal.drilldownAtual = null
  const params = construirParamsAnalise()
  params.set("categoria_id", categoriaId)
  const dados = await api("/stats/mensal-detalhe?" + params.toString())
  if (!dados || dados.length === 0) { document.getElementById("drilldown-vazio").style.display = "flex"; return }
  const cor = estadoGlobal.tipoAtual === "in" ? "#7fc4a0" : "#e08b7f" 
  document.getElementById("grafico-drilldown").style.display = "block"
  estadoGlobal.graficos.drilldown = new Chart(document.getElementById("grafico-drilldown"), {
    type: "bar",
    data: { labels: dados.map(m => fmtMes(m.mes)), datasets: [{ data: dados.map(m => m.total), backgroundColor: cor }] },
    options: {
      aspectRatio: window.innerWidth < 769 ? 1.3 : 2,
      layout: { padding: window.innerWidth < 769 ? { left: 0, right: 0, top: 0, bottom: 0 } : {} },
      plugins: { legend: { display: false }, tooltip: { callbacks: { label: ctx => {
        const idx = ctx.dataIndex; let linha = ` ${fmt(ctx.raw, estadoGlobal.moedaAnaliseGlobal)}`
        if (idx > 0) { const ant = dados[idx-1].total; if (ant > 0) { const v = ((dados[idx].total - ant) / ant) * 100; linha += ` (${v >= 0 ? '+' : ''}${v.toFixed(0)}% ${t("analise.mes_anterior")})` } }
        return linha
      }}}},
      scales: { x: { grid: { display: false }, ticks: { autoSkip: true, maxTicksLimit: window.innerWidth < 769 ? 4 : 8 } }, y: { display: window.innerWidth >= 769, border: { display: false }, ticks: { maxTicksLimit: 6 } } }
    }
  })
}

export function fecharDrillDown() {
  document.getElementById("modal-drilldown").classList.remove("open")
  destruirGrafico("drilldown")
  estadoGlobal.drilldownAtual = null
}

// ─── Padrões recorrentes ─────────────────────────────────
export function ordenarRecorrentes(campo) {
  estadoGlobal.ordenacaoRecorrentes.campo === campo ? estadoGlobal.ordenacaoRecorrentes.direcao *= -1 : (estadoGlobal.ordenacaoRecorrentes.campo = campo, estadoGlobal.ordenacaoRecorrentes.direcao = 1)
  renderizarTabelaRecorrentes()
}
function renderizarRecorrentes(recorrentes) { estadoGlobal.recorrentesTabelaCache = recorrentes; renderizarTabelaRecorrentes() }
export function renderizarTabelaRecorrentes() {
  let lista = [...estadoGlobal.recorrentesTabelaCache]
  renderizarPainelOrdenar("an-recorrentes")
  const { campo, direcao } = estadoGlobal.ordenacaoRecorrentes
  if (campo) lista.sort((a, b) => { let va = a[campo], vb = b[campo]; if (typeof va === "string") { va = va.toLowerCase(); vb = vb.toLowerCase() }; return va < vb ? -direcao : va > vb ? direcao : 0 })
  atualizarIconesOrdenacao("cabecalho-recorrentes", estadoGlobal.ordenacaoRecorrentes)
  const tb = document.getElementById("tabela-recorrentes")
  if (lista.length === 0) {
    tb.innerHTML = temFiltrosAnaliseAtivos()
      ? linhaVazia(5, null, t("analise.recorrentes.sem_resultado"), `<button class="btn-sm" onclick="limparFiltrosAnalise()">${t("contas.vazio.limpar_filtro")}</button>`)
      : linhaVazia(5, null, t("analise.recorrentes.sem_dados"))
    return
  }
  tb.innerHTML = ""
  lista.forEach(r => {
    const nomeCat = nomeCategoria(r.categoria, r.categoria_slug)
    const nomeGrupo = nomeCategoria(r.grupo, r.grupo_slug)
    const frequencia = r.regular ? `~${r.intervalo_medio_dias} ${t("analise.dias_sufixo")}` : `${r.intervalo_medio_dias} ${t("analise.dias_sufixo")} ${t("analise.irregular_sufixo")}`
    tb.innerHTML += `<tr class="linha-expandivel" onclick="toggleLinhaExpandida(this)"><td data-label="${t("movimentos.coluna.descricao")}">${escapeHtml(r.descricao)}</td><td data-label="${t("movimentos.coluna.categoria")}" class="td-expandido"><div class="valor-com-sub"><span>${escapeHtml(nomeCat)}</span><span class="sub-linha"><span class="separador-mobile">· </span>${escapeHtml(nomeGrupo)}</span></div></td><td data-label="${t("analise.coluna.valor_medio")}" style="text-align:right" class="negativo">${fmt(r.valor_medio, estadoGlobal.moedaAnaliseGlobal)}</td><td data-label="${t("analise.coluna.frequencia")}" style="${r.regular ? '' : 'color:var(--color-text-faint)'}">${frequencia}</td><td data-label="${t("analise.coluna.proxima_data")}" class="td-expandido">${fmtData(r.proxima_data_estimada)}</td></tr>`
  })
}
