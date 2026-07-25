import { pararDetecaoInatividade } from './auth.js'
import { guardarConta } from './contas.js'
import { API, estadoGlobal } from './estado.js'
import { nomesMesesAbrev, t, traduzirErro } from './i18n.js'
import { mostrarToast } from './ui.js'

// UTILS GERAIS
// ═══════════════════════════════════════════════════════════
export function fmt(v, moeda) {
  if (estadoGlobal.valoresOcultos) return "••••••"
  return parseFloat(v).toLocaleString("pt-PT", { style: "currency", currency: moeda || "EUR" })
}
export function fmtData(dataIso) {
  if (!dataIso) return ""
  const [ano, mes, dia] = dataIso.split("-")
  return `${dia}-${mes}-${ano}`
}
export function moedaPredominante(lista) {
  if (!lista || lista.length === 0) return "EUR"
  const contagem = {}
  lista.forEach(c => { contagem[c.moeda] = (contagem[c.moeda] || 0) + 1 })
  return Object.entries(contagem).sort((a, b) => b[1] - a[1])[0][0]
}
export function fmtMes(ym) {
  const [y, m] = ym.split("-")
  return nomesMesesAbrev()[parseInt(m)-1] + " " + y.slice(-2)
}
export function fmtDiaCurto(iso) {
  const [y, m, d] = iso.split("-")
  return `${d} ${nomesMesesAbrev()[parseInt(m)-1]}`
}
export function fmtDiaCompleto(iso) {
  const [y, m, d] = iso.split("-")
  return `${d} ${nomesMesesAbrev()[parseInt(m)-1]} ${y}`
}
export function isoDateStr(d) {
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`
}
export function somarDiasIso(dataStr, dias) {
  const [ano, mes, dia] = dataStr.split('-').map(Number)
  const d = new Date(Date.UTC(ano, mes - 1, dia))
  d.setUTCDate(d.getUTCDate() + dias)
  return d.toISOString().slice(0, 10)
}
export function api(path) {
  return fetch(API + path, { headers: { "Authorization": "Bearer " + estadoGlobal.TOKEN } })
    .then(async r => {
      if (r.status === 401) { sessaoExpirada(); throw new Error("Sessão expirada") }
      if (!r.ok) { throw new Error(mensagemDeErro(await r.json().catch(() => ({})))) }
      return r.json()
    })
    .catch(erro => {
      if (erro.message !== "Sessão expirada") mostrarToast(t("toast.sem_ligacao_servidor"), "erro")
      throw erro
    })
}
function sessaoExpirada() {
  pararDetecaoInatividade()
  localStorage.clear(); estadoGlobal.TOKEN = null; estadoGlobal.NOME = null
  document.getElementById("app-screen").style.display  = "none"
  document.getElementById("auth-screen").style.display = "flex"
  mostrarToast(t("toast.sessao_expirou"), "info")
}
// apiPost/apiPut/apiDelete devolvem a Response por tratar (ao contrário de api(), que só
// serve GETs) — várias chamadas precisam de inspeccionar r.status/r.ok elas próprias (ex.
// guardarConta trata o código 409 de forma diferente de um erro normal), por isso não dava
// para responder automaticamente aqui como o api() faz para tudo. O que faltava, e que isto
// acrescenta, é o mesmo tratamento de sessão expirada e de falha de rede que o api() já
// tinha: sem isto, um 401 aqui mostrava um erro genérico em vez de reencaminhar para o
// login, e ficar offline a meio de um POST/PUT/DELETE falhava em silêncio (uma promise
// rejeitada sem nenhum aviso ao utilizador) — só os GETs, via api(), tratavam dos dois.
// O "if (estadoGlobal.TOKEN)" importa: apiPost também serve /login e /registro, sem sessão nenhuma
// ainda — um 401 aí é "credenciais inválidas", não "sessão expirada" (apanhado a sério
// pelo teste E2E de login com password errada, que falhava sem esta condição).
function comSessaoERedeTratadas(pedido) {
  return pedido
    .then(r => {
      if (r.status === 401 && estadoGlobal.TOKEN) { sessaoExpirada(); throw new Error("Sessão expirada") }
      return r
    })
    .catch(erro => {
      if (erro.message !== "Sessão expirada") mostrarToast(t("toast.sem_ligacao_servidor"), "erro")
      throw erro
    })
}
export function apiPost(path, body) {
  return comSessaoERedeTratadas(
    fetch(API + path, { method: "POST", headers: { "Content-Type": "application/json", "Authorization": "Bearer " + estadoGlobal.TOKEN }, body: JSON.stringify(body) })
  )
}
export function apiPut(path, body) {
  return comSessaoERedeTratadas(
    fetch(API + path, { method: "PUT", headers: { "Content-Type": "application/json", "Authorization": "Bearer " + estadoGlobal.TOKEN }, body: JSON.stringify(body) })
  )
}
export function apiDelete(path) {
  return comSessaoERedeTratadas(
    fetch(API + path, { method: "DELETE", headers: { "Authorization": "Bearer " + estadoGlobal.TOKEN } })
  )
}
export async function comBotaoDesativado(btn, fn) {
  btn.disabled = true
  try { await fn() } finally { btn.disabled = false }
}
export function destruirGrafico(nome) {
  if (estadoGlobal.graficos[nome]) { estadoGlobal.graficos[nome].destroy(); delete estadoGlobal.graficos[nome] }
}
document.addEventListener('touchstart', (e) => {
  if (e.target.closest('canvas')) return
  Object.values(estadoGlobal.graficos).forEach(chart => {
    if (!chart) return
    chart.setActiveElements([])
    chart.tooltip?.setActiveElements([], { x: 0, y: 0 })
    chart.update()
  })
}, { passive: true })
export function carregarFiltrosSalvos(pagina) {
  try { return JSON.parse(localStorage.getItem("filtros_" + pagina)) } catch { return null }
}
export function guardarFiltrosPagina(pagina, dados) {
  localStorage.setItem("filtros_" + pagina, JSON.stringify(dados))
}
export function fecharModal() {
  document.querySelectorAll(".modal-overlay:not(#modal-configuracoes)").forEach(m => m.classList.remove("open"))
}
export function mensagemDeErro(d) {
  // contrato actual: detail = {code, message, ctx}. Mantém o fallback de string para
  // respostas que não passam pelo nosso erro_http (ex: 500 não tratado do FastAPI).
  // traduzirErro() só traduz se já houver entrada para o code na língua actual — sem
  // isso cai sempre no message (em português) que o backend já devolve.
  if (d.detail && typeof d.detail === "object" && d.detail.message) return traduzirErro(d.detail)
  if (typeof d.detail === "string") return d.detail
  return t("erro.inesperado")
}
export function codigoErro(d) {
  return (d.detail && typeof d.detail === "object") ? d.detail.code : null
}
export function debounce(fn, atraso = 250) {
  let temporizador
  return (...args) => {
    clearTimeout(temporizador)
    temporizador = setTimeout(() => fn(...args), atraso)
  }
}
export function escapeHtml(texto) {
  return String(texto ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;")
}
// para argumentos de string passados a onclick="funcao(...)" — gera um literal JS
// válido (via JSON.stringify) e depois escapa para poder viver dentro de um atributo HTML.
export function attrJs(valor) {
  return JSON.stringify(valor ?? "").replace(/&/g, "&amp;").replace(/"/g, "&quot;")
}

// ═══════════════════════════════════════════════════════════
