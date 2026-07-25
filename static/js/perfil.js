import { logout } from './auth.js'
import { ICONE_ARRASTAR, ICONE_PROTEGIDA, estadoGlobal } from './estado.js'
import { abrirMenuFlutuante, fecharMenusAcoes, renderizarFiltroCategoriaEspaco } from './filtros.js'
import { nomeCategoria, t } from './i18n.js'
import { atualizarAvatar } from './main.js'
import { camposValidos, confirmarAcao, ligarValidacaoFormulario, mostrarToast } from './ui.js'
import { api, apiDelete, apiPost, apiPut, attrJs, codigoErro, escapeHtml, fecharModal, mensagemDeErro } from './utils.js'

// PÁGINA: PERFIL
// ═══════════════════════════════════════════════════════════
export function trocarSecaoPerfil(secao) {
  document.querySelectorAll(".perfil-sidebar-item").forEach(item => item.classList.toggle("active", item.dataset.secao === secao))
  document.querySelectorAll(".perfil-secao").forEach(el => el.classList.toggle("active", el.id === `perfil-secao-${secao}`))
}
export async function carregarConfiguracoes() {
  const dados = await api("/me")
  estadoGlobal.perfilCache = dados
  document.getElementById("perfil-nome-display").textContent = dados.nome
  document.getElementById("perfil-email-display").textContent = dados.email
  await carregarArvoreCategorias()
}
export function abrirModalEditarPerfil() {
  document.getElementById("perfil-nome").value = estadoGlobal.perfilCache.nome
  document.getElementById("perfil-email").value = estadoGlobal.perfilCache.email
  ligarValidacaoFormulario(["perfil-nome", "perfil-email"], "btn-guardar-perfil")
  document.getElementById("modal-editar-perfil").classList.add("open")
}
export function abrirModalAlterarPassword() {
  document.getElementById("perfil-pw-atual").value = ""
  document.getElementById("perfil-pw-nova").value = ""
  ligarValidacaoFormulario(["perfil-pw-atual", "perfil-pw-nova"], "btn-guardar-password")
  document.getElementById("modal-alterar-password").classList.add("open")
}
export async function guardarPerfil() {
  if (!camposValidos("perfil-nome", "perfil-email")) return
  const r = await apiPut("/me", { nome: document.getElementById("perfil-nome").value, email: document.getElementById("perfil-email").value })
  const d = await r.json()
  if (!r.ok) { mostrarToast(mensagemDeErro(d), "erro"); return }
  estadoGlobal.NOME = d.nome; localStorage.setItem("nome", estadoGlobal.NOME); atualizarAvatar()
  estadoGlobal.perfilCache = { nome: document.getElementById("perfil-nome").value, email: document.getElementById("perfil-email").value }
  document.getElementById("perfil-nome-display").textContent = estadoGlobal.perfilCache.nome
  document.getElementById("perfil-email-display").textContent = estadoGlobal.perfilCache.email
  fecharModal()
  mostrarToast(t("perfil.msg.perfil_atualizado"), "sucesso")
}
export async function guardarPassword() {
  if (!camposValidos("perfil-pw-atual", "perfil-pw-nova")) return
  const r = await apiPut("/me/password", { password_atual: document.getElementById("perfil-pw-atual").value, password_nova: document.getElementById("perfil-pw-nova").value })
  const d = await r.json()
  if (!r.ok) { mostrarToast(mensagemDeErro(d), "erro"); return }
  estadoGlobal.TOKEN = d.token; localStorage.setItem("token", estadoGlobal.TOKEN)   // <-- mantém a sessão atual válida
  document.getElementById("perfil-pw-atual").value = ""; document.getElementById("perfil-pw-nova").value = ""
  fecharModal()
  mostrarToast(t("perfil.msg.password_atualizada"), "sucesso")
}
export async function terminarTodasAsSessoes() {
  if (!(await confirmarAcao(t("perfil.msg.confirmar_terminar_sessoes")))) return
  const r = await apiPost("/me/sessoes/terminar", {})
  if (!r.ok) { mostrarToast(mensagemDeErro(await r.json()), "erro"); return }
  logout()
  mostrarToast(t("perfil.msg.sessoes_terminadas"), "info")
}
export async function eliminarContaUtilizador() {
  if (!(await confirmarAcao(t("perfil.msg.confirmar_eliminar_conta_1"), { perigo: true }))) return
  if (!(await confirmarAcao(t("perfil.msg.confirmar_eliminar_conta_2"), { textoConfirmar: t("perfil.msg.eliminar_definitivamente"), perigo: true }))) return
  const r = await apiDelete("/me")
  if (!r.ok) { mostrarToast(mensagemDeErro(await r.json()), "erro"); return }
  logout()
}

// ═══════════════════════════════════════════════════════════
// GESTÃO DE CATEGORIAS (PERFIL)
// ═══════════════════════════════════════════════════════════
async function recarregarCategoriasGlobais() {
  estadoGlobal.categoriasCache = await api("/categorias")
  estadoGlobal.arvoreAnaliseCache = await api("/categorias/arvore")
  estadoGlobal.categoriasSelecionadas.clear()
  estadoGlobal.categoriasMovSelecionadas.clear()
  renderizarFiltroCategoriaEspaco("an")
  renderizarFiltroCategoriaEspaco("mov")
}
async function aposMudarCategorias() { await carregarArvoreCategorias(); await recarregarCategoriasGlobais() }
async function carregarArvoreCategorias() { estadoGlobal.arvoreCategoriasCache = await api("/categorias/arvore"); renderizarArvoreCategorias() }

export function trocarTipoCategorias(tipo) {
  estadoGlobal.tipoGestaoCategorias = tipo
  document.getElementById("cat-tipo-in").classList.toggle("active", tipo === "in")
  document.getElementById("cat-tipo-out").classList.toggle("active", tipo === "out")
  renderizarArvoreCategorias()
}
function renderizarArvoreCategorias() {
  const grupos = estadoGlobal.arvoreCategoriasCache.filter(g => estadoGlobal.tipoGestaoCategorias === "in" ? g.eh_recebimento : !g.eh_recebimento)
  const el = document.getElementById("lista-categorias-gestao")
  if (grupos.length === 0) {
    const chaveVazio = estadoGlobal.tipoGestaoCategorias === "in" ? "perfil.categorias.sem_grupos_entradas" : "perfil.categorias.sem_grupos_saidas"
    el.innerHTML = `<div class="estado-vazio"><div class="subtitulo">${t(chaveVazio)}</div></div>`
    return
  }
  el.innerHTML = ""
  grupos.forEach((g, gi) => {
    const grupoProtegido = g.categorias.some(c => c.protegida)
    const tagGrupoProtegido = grupoProtegido ? `<span class="icone-protegida" id="grupo-protegido-${g.id}" data-ajuda="${t("perfil.categorias.grupo_protegido_ajuda")}">${ICONE_PROTEGIDA}</span>` : ""
    el.innerHTML += `<div class="grupo-gestao" ondragend="arrastarFim(event)" ondragover="arrastarSobre(event,'grupo',${g.id})" ondrop="largarSobre(event,'grupo',${g.id},null)"><div class="grupo-gestao-header"><span style="display:flex;align-items:center"><span class="arraste-alca" draggable="true" ondragstart="arrastarInicio(event,'grupo',${g.id},null)">${ICONE_ARRASTAR}</span><span class="nome">${escapeHtml(nomeCategoria(g.nome, g.slug))}${tagGrupoProtegido}</span></span><div class="acoes"><button class="btn-sm btn-icone-only" onclick="abrirModalCategoria(${g.id})" aria-label="${t("perfil.categorias.adicionar_categoria_aria")}">+</button><button class="btn-sm" onclick="toggleMenuAcoesGrupo(event, ${g.id}, ${attrJs(g.nome)}, ${grupoProtegido}, ${gi === 0}, ${gi === grupos.length - 1})" aria-label="${t("contas.acoes.mais_acoes")}">⋮</button></div></div><div class="categorias-gestao-lista">${g.categorias.map((c, ci) => {
      const tagProtegida = c.protegida ? `<span class="icone-protegida" id="cat-protegida-${c.id}" data-ajuda="${t("perfil.categorias.categoria_protegida_ajuda")}">${ICONE_PROTEGIDA}</span>` : ""
      return `<div class="categoria-gestao-item" ondragend="arrastarFim(event)" ondragover="arrastarSobre(event,'categoria',${c.id})" ondrop="largarSobre(event,'categoria',${c.id},${g.id})"><span style="display:flex;align-items:center"><span class="arraste-alca" draggable="true" ondragstart="arrastarInicio(event,'categoria',${c.id},${g.id})">${ICONE_ARRASTAR}</span><span>${escapeHtml(nomeCategoria(c.nome, c.slug))}${tagProtegida}</span></span><div class="acoes"><button class="btn-sm" onclick="toggleMenuAcoesCategoria(event, ${c.id}, ${attrJs(c.nome)}, ${g.id}, ${c.protegida}, ${ci === 0}, ${ci === g.categorias.length - 1})" aria-label="${t("contas.acoes.mais_acoes")}">⋮</button></div></div>`
    }).join("")}</div></div>`
  })
}

let arrastoAtual = null   // { tipo: 'grupo'|'categoria', id, grupoId }

export function arrastarInicio(e, tipo, id, grupoId) {
  arrastoAtual = { tipo, id, grupoId }
  e.dataTransfer.effectAllowed = "move"
  e.target.closest(tipo === "grupo" ? ".grupo-gestao" : ".categoria-gestao-item").classList.add("a-arrastar")
}
export function arrastarFim() {
  document.querySelectorAll(".a-arrastar").forEach(el => el.classList.remove("a-arrastar"))
  document.querySelectorAll(".arraste-acima, .arraste-abaixo").forEach(el => el.classList.remove("arraste-acima", "arraste-abaixo"))
}
export function arrastarSobre(e, tipo, id) {
  if (!arrastoAtual || arrastoAtual.tipo !== tipo || arrastoAtual.id === id) return
  e.preventDefault()
  const alvo = e.currentTarget
  const rect = alvo.getBoundingClientRect()
  const emCima = (e.clientY - rect.top) < rect.height / 2
  document.querySelectorAll(".arraste-acima, .arraste-abaixo").forEach(el => el.classList.remove("arraste-acima", "arraste-abaixo"))
  alvo.classList.add(emCima ? "arraste-acima" : "arraste-abaixo")
}
export function toggleMenuAcoesGrupo(event, id, nome, protegido, ehPrimeiro, ehUltimo) {
  const mover = `${ehPrimeiro ? "" : `<button onclick="fecharMenusAcoes(); moverItemCategoria('grupo', ${id}, null, -1)">${t("perfil.categorias.mover_para_cima")}</button>`}${ehUltimo ? "" : `<button onclick="fecharMenusAcoes(); moverItemCategoria('grupo', ${id}, null, 1)">${t("perfil.categorias.mover_para_baixo")}</button>`}`
  abrirMenuFlutuante(event, "grupoId", id, `
    ${mover}
    ${mover ? `<div class="menu-acoes-separador"></div>` : ""}
    <button onclick="fecharMenusAcoes(); abrirEditarGrupo(${id},${attrJs(nome)})">${t("generico.editar")}</button>
    ${protegido ? "" : `<button class="perigo" onclick="fecharMenusAcoes(); confirmarEliminarCategoria(${id}, true)">${t("generico.eliminar")}</button>`}
  `)
}
export function toggleMenuAcoesCategoria(event, id, nome, grupoId, protegido, ehPrimeiro, ehUltimo) {
  const mover = `${ehPrimeiro ? "" : `<button onclick="fecharMenusAcoes(); moverItemCategoria('categoria', ${id}, ${grupoId}, -1)">${t("perfil.categorias.mover_para_cima")}</button>`}${ehUltimo ? "" : `<button onclick="fecharMenusAcoes(); moverItemCategoria('categoria', ${id}, ${grupoId}, 1)">${t("perfil.categorias.mover_para_baixo")}</button>`}`
  abrirMenuFlutuante(event, "categoriaId", id, `
    ${mover}
    ${mover && !protegido ? `<div class="menu-acoes-separador"></div>` : ""}
    ${protegido ? "" : `<button onclick="fecharMenusAcoes(); abrirEditarCategoriaGestao(${id},${attrJs(nome)},${grupoId})">${t("generico.editar")}</button><button class="perigo" onclick="fecharMenusAcoes(); confirmarEliminarCategoria(${id}, false)">${t("generico.eliminar")}</button>`}
  `)
}
export async function moverItemCategoria(tipo, id, grupoId, direcao) {
  let lista
  if (tipo === "grupo") {
    lista = estadoGlobal.arvoreCategoriasCache.filter(g => estadoGlobal.tipoGestaoCategorias === "in" ? g.eh_recebimento : !g.eh_recebimento).map(g => g.id)
  } else {
    lista = estadoGlobal.arvoreCategoriasCache.find(g => g.id === grupoId).categorias.map(c => c.id)
  }
  const idx = lista.indexOf(id)
  const novoIdx = idx + direcao
  if (novoIdx < 0 || novoIdx >= lista.length) return
  ;[lista[idx], lista[novoIdx]] = [lista[novoIdx], lista[idx]]
  fecharMenusAcoes()
  const r = await apiPut("/categorias/reordenar", { ids: lista })
  if (!r.ok) { mostrarToast(mensagemDeErro(await r.json()), "erro"); return }
  carregarArvoreCategorias()
}
export async function largarSobre(e, tipo, idAlvo, grupoIdAlvo) {
  e.preventDefault()
  if (!arrastoAtual || arrastoAtual.tipo !== tipo || arrastoAtual.id === idAlvo) return
  const alvo = e.currentTarget
  const emCima = alvo.classList.contains("arraste-acima")
  arrastarFim()

  let lista
  if (tipo === "grupo") {
    lista = estadoGlobal.arvoreCategoriasCache.filter(g => estadoGlobal.tipoGestaoCategorias === "in" ? g.eh_recebimento : !g.eh_recebimento).map(g => g.id)
  } else {
    lista = estadoGlobal.arvoreCategoriasCache.find(g => g.id === grupoIdAlvo).categorias.map(c => c.id)
  }

  const origemIdx = lista.indexOf(arrastoAtual.id)
  lista.splice(origemIdx, 1)
  let destinoIdx = lista.indexOf(idAlvo)
  if (!emCima) destinoIdx += 1
  lista.splice(destinoIdx, 0, arrastoAtual.id)

  arrastoAtual = null
  const r = await apiPut("/categorias/reordenar", { ids: lista })
  if (!r.ok) { mostrarToast(mensagemDeErro(await r.json()), "erro"); return }
  carregarArvoreCategorias()
}

export function abrirModalGrupo() {
  document.getElementById("modal-grupo-titulo").textContent = t("modal_grupo.titulo_adicionar"); document.getElementById("grupo-id").value = ""; document.getElementById("grupo-nome").value = ""; document.getElementById("grupo-tipo").value = estadoGlobal.tipoGestaoCategorias; document.getElementById("grupo-tipo-campo").style.display = ""
  document.getElementById("modal-grupo").classList.add("open"); ligarValidacaoFormulario(["grupo-nome"], "btn-guardar-grupo")
}
export function abrirEditarGrupo(id, nome) {
  document.getElementById("modal-grupo-titulo").textContent = t("modal_grupo.titulo_editar"); document.getElementById("grupo-id").value = id; document.getElementById("grupo-nome").value = nome; document.getElementById("grupo-tipo-campo").style.display = "none"
  document.getElementById("modal-grupo").classList.add("open"); ligarValidacaoFormulario(["grupo-nome"], "btn-guardar-grupo")
}
export async function guardarGrupo() {
  if (!camposValidos("grupo-nome")) return
  const id = document.getElementById("grupo-id").value, nome = document.getElementById("grupo-nome").value
  let r
  if (id) { r = await apiPut("/categorias/" + id, { nome }) }
  else     { r = await apiPost("/categorias", { nome, eh_recebimento: document.getElementById("grupo-tipo").value === "in" }) }
  if (!r.ok) { mostrarToast(mensagemDeErro(await r.json()), "erro"); return }
  fecharModal(); aposMudarCategorias()
}
function preencherSelectGrupos(grupoSelecionadoId) {
  const sel = document.getElementById("categoria-gestao-grupo"); sel.innerHTML = ""
  estadoGlobal.arvoreCategoriasCache.filter(g => estadoGlobal.tipoGestaoCategorias === "in" ? g.eh_recebimento : !g.eh_recebimento).forEach(g => {
    sel.innerHTML += `<option value="${g.id}" ${g.id === grupoSelecionadoId ? "selected" : ""}>${escapeHtml(nomeCategoria(g.nome, g.slug))}</option>`
  })
}
export function abrirModalCategoria(grupoId) {
  document.getElementById("modal-categoria-gestao-titulo").textContent = t("modal_categoria.titulo_adicionar"); document.getElementById("categoria-gestao-id").value = ""; document.getElementById("categoria-gestao-nome").value = ""; preencherSelectGrupos(grupoId)
  document.getElementById("modal-categoria-gestao").classList.add("open"); ligarValidacaoFormulario(["categoria-gestao-nome"], "btn-guardar-categoria-gestao")
}
export function abrirEditarCategoriaGestao(id, nome, grupoId) {
  document.getElementById("modal-categoria-gestao-titulo").textContent = t("modal_categoria.titulo_editar"); document.getElementById("categoria-gestao-id").value = id; document.getElementById("categoria-gestao-nome").value = nome; preencherSelectGrupos(grupoId)
  document.getElementById("modal-categoria-gestao").classList.add("open"); ligarValidacaoFormulario(["categoria-gestao-nome"], "btn-guardar-categoria-gestao")
}
export async function guardarCategoriaGestao() {
  if (!camposValidos("categoria-gestao-nome")) return
  const id = document.getElementById("categoria-gestao-id").value, nome = document.getElementById("categoria-gestao-nome").value, grupoId = parseInt(document.getElementById("categoria-gestao-grupo").value)
  let r
  if (id) { r = await apiPut("/categorias/" + id, { nome, parent_id: grupoId }) }
  else     { r = await apiPost("/categorias", { nome, parent_id: grupoId }) }
  if (!r.ok) { mostrarToast(mensagemDeErro(await r.json()), "erro"); return }
  fecharModal(); aposMudarCategorias()
}
export async function confirmarEliminarCategoria(id, ehGrupo) {
  estadoGlobal.elimAtual = id
  const r = await apiDelete("/categorias/" + id)
  if (r.ok) { aposMudarCategorias(); return }
  const d = await r.json()
  // só faz sentido oferecer migrar/forçar quando o motivo é mesmo "tem dependentes" —
  // uma categoria protegida (ou outro erro qualquer) não se resolve dessa forma.
  const temOpcaoDeMigrarOuForcar = ["CATEGORIA_COM_MOVIMENTOS", "GRUPO_COM_CATEGORIAS"].includes(codigoErro(d))
  if (!temOpcaoDeMigrarOuForcar) { mostrarToast(mensagemDeErro(d), "erro"); return }
  document.getElementById("elim-titulo").textContent = ehGrupo ? t("modal_eliminar_cat.titulo_grupo") : t("modal_eliminar_cat.titulo_categoria")
  document.getElementById("elim-aviso").textContent  = mensagemDeErro(d)
  const selectMigrar = document.getElementById("elim-migrar-para"); selectMigrar.innerHTML = ""
  if (ehGrupo) {
    const grupo = estadoGlobal.arvoreCategoriasCache.find(g => g.id === id)
    estadoGlobal.arvoreCategoriasCache.filter(g => g.id !== id && g.eh_recebimento === grupo.eh_recebimento).forEach(g => selectMigrar.innerHTML += `<option value="${g.id}">${escapeHtml(nomeCategoria(g.nome, g.slug))}</option>`)
  } else {
    const grupoPai = estadoGlobal.arvoreCategoriasCache.find(g => g.categorias.some(c => c.id === id))
    grupoPai.categorias.filter(c => c.id !== id).forEach(c => selectMigrar.innerHTML += `<option value="${c.id}">${escapeHtml(nomeCategoria(c.nome, c.slug))}</option>`)
  }
  document.getElementById("modal-eliminar-categoria").classList.add("open")
}
export async function confirmarEliminacaoForcada() {
  if (!(await confirmarAcao(t("modal_eliminar_cat.confirmar_forcar"), { perigo: true }))) return
  await apiDelete("/categorias/" + estadoGlobal.elimAtual + "?forcar=true"); fecharModal(); aposMudarCategorias()
}
export async function confirmarEliminacaoComMigracao() {
  await apiDelete("/categorias/" + estadoGlobal.elimAtual + "?migrar_para_id=" + document.getElementById("elim-migrar-para").value); fecharModal(); aposMudarCategorias()
}

// ═══════════════════════════════════════════════════════════
