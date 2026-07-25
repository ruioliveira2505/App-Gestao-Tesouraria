import { definirDataCalendarioSimples } from './calendario.js'
import { toggleLinhaExpandida } from './contas.js'
import { ICONE_INFO, estadoGlobal } from './estado.js'
import { atualizarVisibilidadeLimparMovimentos, limparFiltrosMovimentos, renderizarSeletorCategoriaMovForm, renderizarSeletorConta, renderizarSeletorTipoMovForm, selecionarCategoriaMovForm, selecionarContaMovForm, selecionarTipoMovForm, temFiltrosMovimentosAtivos, toggleMenuAcoesMovimento } from './filtros.js'
import { nomeCategoria, t } from './i18n.js'
import { atualizarIconesOrdenacao, renderizarPainelOrdenar } from './ordenacao.js'
import { camposValidos, confirmarAcao, ligarValidacaoMovimento, linhaVazia, linhasEsqueleto, mostrarToast } from './ui.js'
import { api, apiDelete, apiPost, apiPut, debounce, escapeHtml, fecharModal, fmt, fmtData, guardarFiltrosPagina, isoDateStr, mensagemDeErro } from './utils.js'

// PÁGINA: MOVIMENTOS
// ═══════════════════════════════════════════════════════════
export async function carregarMovimentos() {
  document.getElementById("tabela-movimentos").innerHTML = linhasEsqueleto(6, 4)
  const contasSel = estadoGlobal.contasSelecionadas.mov
  const categorias = estadoGlobal.categoriasMovSelecionadas
  atualizarVisibilidadeLimparMovimentos()
  guardarFiltrosPagina("movimentos", { contas: [...contasSel], categorias: [...categorias], dataDe: estadoGlobal.movDataDe, dataAte: estadoGlobal.movDataAte })
  const params = new URLSearchParams()
  if (contasSel.size > 0) params.set("conta_id", [...contasSel].join(","))
  if (categorias.size > 0) params.set("categoria_id", [...categorias].join(","))
  if (estadoGlobal.movDataDe)  params.set("data_de", estadoGlobal.movDataDe)
  if (estadoGlobal.movDataAte) params.set("data_ate", estadoGlobal.movDataAte)
  if (estadoGlobal.pendentesAtivo) params.set("precisa_confirmacao", "true")
  const qs = params.toString() ? "?" + params.toString() : ""
  estadoGlobal.movimentosCache = estadoGlobal.movimentosTabelaCache = await api("/movimentos" + qs)
  renderizarTabelaMovimentos(); atualizarBadgePendentes()
}

export function ordenarMovimentos(campo) {
  estadoGlobal.ordenacaoMovimentos.campo === campo ? estadoGlobal.ordenacaoMovimentos.direcao *= -1 : (estadoGlobal.ordenacaoMovimentos.campo = campo, estadoGlobal.ordenacaoMovimentos.direcao = 1)
  renderizarTabelaMovimentos()
}
export function renderizarTabelaMovimentos() {
  let lista = [...estadoGlobal.movimentosTabelaCache]
  atualizarVisibilidadeLimparMovimentos()
  renderizarPainelOrdenar("mov")
  const pesquisa = document.getElementById("filtro-pesquisa").value.trim().toLowerCase()
  if (pesquisa) lista = lista.filter(m => m.descricao.toLowerCase().includes(pesquisa))
  const { campo, direcao } = estadoGlobal.ordenacaoMovimentos
  if (campo) lista.sort((a, b) => {
    let va, vb
    if (campo === "conta") { const ca = estadoGlobal.contasCache.find(c => c.id === a.conta_id), cb = estadoGlobal.contasCache.find(c => c.id === b.conta_id); va = ca ? ca.nome : a.conta_id; vb = cb ? cb.nome : b.conta_id }
    else { va = a[campo]; vb = b[campo] }
    if (typeof va === "string") { va = va.toLowerCase(); vb = vb.toLowerCase() }
    return va < vb ? -direcao : va > vb ? direcao : 0
  })
  atualizarIconesOrdenacao("cabecalho-movimentos", estadoGlobal.ordenacaoMovimentos)
  const tb = document.getElementById("tabela-movimentos")
  if (lista.length === 0) {
    tb.innerHTML = temFiltrosMovimentosAtivos()
      ? linhaVazia(6, null, t("movimentos.vazio.nenhum_encontrado"), `<button class="btn-sm" onclick="limparFiltrosMovimentos()">${t("movimentos.vazio.limpar_filtros")}</button>`)
      : linhaVazia(6, null, t("movimentos.vazio.sem_movimentos"), `<button class="btn-primary" onclick="abrirModalMovimento()">${t("movimentos.vazio.adicionar")}</button>`)
    return
  }
  tb.innerHTML = ""
  lista.forEach(m => {
    const conta = estadoGlobal.contasCache.find(c => c.id === m.conta_id)
    const pendente = !m.confirmado

    tb.innerHTML += `<tr class="linha-expandivel${pendente ? ' linha-pendente' : ''}" onclick="toggleLinhaExpandida(this)"><td data-label="${t("movimentos.coluna.data")}">${fmtData(m.data)}</td><td data-label="${t("movimentos.coluna.descricao")}">${escapeHtml(m.descricao)}</td><td data-label="${t("movimentos.coluna.conta")}" class="td-expandido"><div class="valor-com-sub"><span>${escapeHtml(conta ? conta.nome : m.conta_id)}</span>${conta && conta.banco ? `<span class="sub-linha"><span class="separador-mobile">· </span>${escapeHtml(conta.banco)}</span>` : ""}</div></td><td data-label="${t("movimentos.coluna.categoria")}" class="td-expandido"><div class="valor-com-sub"><span>${escapeHtml(nomeCategoria(m.categoria, m.categoria_slug))}</span>${m.grupo ? `<span class="sub-linha"><span class="separador-mobile">· </span>${escapeHtml(nomeCategoria(m.grupo, m.grupo_slug))}</span>` : ""}</div></td><td data-label="${t("movimentos.coluna.valor")}" style="text-align:right" class="${m.valor >= 0 ? 'positivo' : 'negativo'}">${fmt(m.valor, conta?.moeda)}</td><td class="td-acoes td-expandido" style="white-space:nowrap">
      <span class="acoes-desktop">
        <button class="btn-sm" onclick="event.stopPropagation(); toggleMenuAcoesMovimento(event, '${m.id}')" aria-label="${t("contas.acoes.mais_acoes")}">⋮</button>
      </span>
      ${pendente ? `<button class="btn-confirmar" onclick="event.stopPropagation(); confirmarMovimento('${m.id}')">✓<span class="btn-confirmar-texto"> ${t("movimentos.confirmar")}</span></button>` : ""}
      <span class="acoes-mobile">
        <button class="btn-sm" onclick="event.stopPropagation(); abrirEditarMovimento('${m.id}')">${t("contas.acoes.editar")}</button>
        <button class="btn-danger" onclick="event.stopPropagation(); eliminarMovimento('${m.id}')" aria-label="${t("movimentos.eliminar_aria")}">✕</button>
      </span>
    </td></tr>`
  })
}
// evita reconstruir a tabela inteira a cada tecla premida — só depois de 250ms sem digitar
export const renderizarTabelaMovimentosDebounced = debounce(renderizarTabelaMovimentos, 250)

export function abrirModalMovimento() {
  document.getElementById("modal-movimento-titulo").textContent = t("modal_movimento.titulo_adicionar")
  document.getElementById("mov-id").value = ""
  definirDataCalendarioSimples("mov-data", isoDateStr(new Date()))
  document.getElementById("mov-descricao").value = ""
  document.getElementById("mov-valor").value = ""

  document.getElementById("mov-conta").value = ""
  document.getElementById("mov-conta-display").value = ""
  renderizarSeletorConta(null)

  document.getElementById("mov-tipo").value = ""
  document.getElementById("mov-tipo-display").value = ""
  renderizarSeletorTipoMovForm(null)

  document.getElementById("mov-categoria").value = ""
  document.getElementById("mov-categoria-display").value = ""
  renderizarSeletorCategoriaMovForm(null)

  document.getElementById("modal-movimento").classList.add("open")
  ligarValidacaoMovimento()
}

export function abrirEditarMovimento(id) {
  const m = estadoGlobal.movimentosCache.find(x => x.id === id); if (!m) return
  document.getElementById("modal-movimento-titulo").textContent = t("modal_movimento.titulo_editar")
  document.getElementById("mov-id").value = m.id
  selecionarContaMovForm(m.conta_id)
  definirDataCalendarioSimples("mov-data", m.data)
  document.getElementById("mov-descricao").value = m.descricao
  document.getElementById("mov-valor").value = Math.abs(m.valor)
  const tipo = m.valor > 0 ? "in" : "out"
  selecionarTipoMovForm(tipo)
  selecionarCategoriaMovForm(m.categoria_id)
  document.getElementById("modal-movimento").classList.add("open")
  ligarValidacaoMovimento()
}
export async function guardarMovimento() {
  if (!camposValidos("mov-descricao", "mov-valor", "mov-categoria-display", "mov-data")) return
  const id = document.getElementById("mov-id").value, tipo = document.getElementById("mov-tipo").value
  const magnitude = Math.abs(parseFloat(document.getElementById("mov-valor").value))
  const body = { conta_id: document.getElementById("mov-conta").value, data: document.getElementById("mov-data-iso").value, descricao: document.getElementById("mov-descricao").value, valor: tipo === "in" ? magnitude : -magnitude, categoria_id: parseInt(document.getElementById("mov-categoria").value) }
  const r = id ? await apiPut("/movimentos/" + id, body) : await apiPost("/movimentos", body)
  if (!r.ok) { mostrarToast(mensagemDeErro(await r.json()), "erro"); return }
  fecharModal(); carregarMovimentos()
}
export async function eliminarMovimento(id) {
  if (!(await confirmarAcao(t("movimentos.confirmar_eliminar"), { perigo: true }))) return
  const r = await apiDelete("/movimentos/" + id)
  if (!r.ok) { mostrarToast(mensagemDeErro(await r.json()), "erro"); return }
  carregarMovimentos()
}

export async function atualizarBadgePendentes() {
  const r = await api("/movimentos/pendentes/contagem")
  const badge = document.getElementById("badge-pendentes")
  if (r.contagem > 0) { badge.textContent = r.contagem; badge.style.display = "inline-flex" } else { badge.style.display = "none" }
  renderizarBannerPendentes(r.contagem)
}
function renderizarBannerPendentes(contagem) {
  const banner = document.getElementById("banner-pendentes"), texto = document.getElementById("banner-pendentes-texto"), acoes = banner.querySelector(".acoes")
  if (estadoGlobal.pendentesAtivo) {
    texto.textContent = t("movimentos.pendentes.a_mostrar_so_pendentes")
    acoes.innerHTML = `<button class="btn-primary" onclick="confirmarTodosPendentes()">${t("movimentos.pendentes.confirmar_todos")}</button><button class="btn-secondary" onclick="limparModoPendentes()">${t("movimentos.pendentes.ver_todos")}</button>`
    banner.style.display = "flex"
  } else if (contagem > 0) {
    texto.innerHTML = `<span class="icone-protegida" id="banner-pendentes-ajuda" data-ajuda="${t("movimentos.pendentes.ajuda")}">${ICONE_INFO}</span> ${contagem} ${t("movimentos.pendentes.contagem_texto")}`
    acoes.innerHTML = `<button class="btn-secondary" onclick="filtrarApenasPendentes()">${t("movimentos.pendentes.ver_pendentes")}</button><button class="btn-primary" onclick="confirmarTodosPendentes()">${t("movimentos.pendentes.confirmar_todos")}</button>`
    banner.style.display = "flex"
  } else { banner.style.display = "none" }
}
export function filtrarApenasPendentes()  { estadoGlobal.pendentesAtivo = true;  carregarMovimentos() }
export function limparModoPendentes()     { estadoGlobal.pendentesAtivo = false; carregarMovimentos() }
export async function confirmarMovimento(id) {
  const r = await apiPost(`/movimentos/${id}/confirmar`, {})
  if (!r.ok) { mostrarToast(mensagemDeErro(await r.json()), "erro"); return }
  carregarMovimentos()
}
export async function confirmarTodosPendentes() {
  if (!(await confirmarAcao(t("movimentos.pendentes.confirmar_todos_pergunta")))) return
  const r = await apiPost("/movimentos/confirmar-todos", {})
  if (!r.ok) { mostrarToast(mensagemDeErro(await r.json()), "erro"); return }
  estadoGlobal.pendentesAtivo = false; carregarMovimentos()
}

// ═══════════════════════════════════════════════════════════
