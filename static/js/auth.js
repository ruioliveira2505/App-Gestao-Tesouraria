import { EVENTOS_ATIVIDADE, TEMPO_INATIVIDADE_MS, estadoGlobal } from './estado.js'
import { iniciarApp } from './main.js'
import { t } from './i18n.js'
import { ligarValidacaoFormulario, mostrarToast } from './ui.js'
import { apiPost, mensagemDeErro } from './utils.js'

// AUTENTICAÇÃO
// ═══════════════════════════════════════════════════════════
export function trocarTab(tab) {
  document.querySelectorAll(".auth-tab").forEach((el, i) => el.classList.toggle("active", (i===0)===(tab==="login")))
  document.getElementById("tab-login").style.display   = tab === "login"   ? "" : "none"
  document.getElementById("tab-registo").style.display = tab === "registo" ? "" : "none"
  document.getElementById("tab-esqueci").style.display = "none"
  document.getElementById("auth-erro").textContent = ""
}
async function corpoOuErro(r, idElementoErro) {
  const d = await r.json()
  if (!r.ok) { document.getElementById(idElementoErro).textContent = mensagemDeErro(d); return null }
  return d
}
export async function fazerLogin() {
  const r = await apiPost("/login", { email: document.getElementById("login-email").value, password: document.getElementById("login-password").value })
  const d = await corpoOuErro(r, "auth-erro")
  if (!d) return
  guardarSessao(d.token, d.nome)
}
export async function fazerRegisto() {
  const r = await apiPost("/registro", { nome: document.getElementById("reg-nome").value, email: document.getElementById("reg-email").value, password: document.getElementById("reg-password").value })
  const d = await corpoOuErro(r, "auth-erro")
  if (!d) return
  guardarSessao(d.token, d.nome)
}
function guardarSessao(token, nome) {
  estadoGlobal.TOKEN = token; estadoGlobal.NOME = nome
  localStorage.setItem("token", token); localStorage.setItem("nome", nome)
  iniciarApp()
}
export function logout() {
  pararDetecaoInatividade()
  localStorage.clear(); estadoGlobal.TOKEN = null; estadoGlobal.NOME = null
  document.getElementById("login-email").value = ""
  document.getElementById("login-password").value = ""
  document.getElementById("app-screen").style.display  = "none"
  document.getElementById("auth-screen").style.display = "flex"
  trocarTab("login")
}
export function abrirEsqueciPassword() {
  document.getElementById("tab-login").style.display   = "none"
  document.getElementById("tab-registo").style.display = "none"
  document.getElementById("tab-esqueci").style.display = ""
  document.querySelectorAll(".auth-tab").forEach(el => el.classList.remove("active"))
}
export async function enviarEsqueciPassword() {
  await apiPost("/esqueci-password", { email: document.getElementById("esqueci-email").value })
  // o backend devolve sempre o mesmo texto fixo (de propósito, para não revelar quais
  // emails existem — ver routers/auth.py) por isso o frontend usa a sua própria tradução
  // em vez de mostrar `d.mensagem`, que vem sempre em português.
  mostrarToast(t("auth.esqueci_password_confirmacao"), "info")
  trocarTab("login")
}
export function verificarTokenReset() {
  const params = new URLSearchParams(window.location.search)
  const token = params.get("token")
  if (!token) return false
  window.RESET_TOKEN = token
  document.querySelectorAll(".auth-card > *:not(#reset-screen)").forEach(el => el.style.display = "none")
  document.getElementById("reset-screen").style.display = "block"
  ligarValidacaoFormulario(["reset-password-nova"], "btn-reset")
  return true
}
export async function submeterRedefinicao() {
  const r = await apiPost("/redefinir-password", { token: window.RESET_TOKEN, password_nova: document.getElementById("reset-password-nova").value })
  const d = await corpoOuErro(r, "reset-erro")
  if (!d) return
  mostrarToast(t("auth.password_redefinida"), "sucesso")
  setTimeout(() => { window.location.href = "/static/index.html" }, 1200)
}

// ═══════════════════════════════════════════════════════════
// INATIVIDADE
// ═══════════════════════════════════════════════════════════
function reiniciarTimerInatividade() {
  clearTimeout(estadoGlobal.timerInatividade)
  estadoGlobal.timerInatividade = setTimeout(logoutPorInatividade, TEMPO_INATIVIDADE_MS)
}
export function iniciarDetecaoInatividade() {
  EVENTOS_ATIVIDADE.forEach(e => document.addEventListener(e, reiniciarTimerInatividade))
  reiniciarTimerInatividade()
}
export function pararDetecaoInatividade() {
  clearTimeout(estadoGlobal.timerInatividade)
  EVENTOS_ATIVIDADE.forEach(e => document.removeEventListener(e, reiniciarTimerInatividade))
}
function logoutPorInatividade() { logout(); mostrarToast(t("toast.sessao_terminada_inatividade"), "info") }

// ═══════════════════════════════════════════════════════════
