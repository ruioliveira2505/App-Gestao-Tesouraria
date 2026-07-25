import { ICONE_TOAST_ERRO, ICONE_TOAST_SUCESSO } from './estado.js'
import { t } from './i18n.js'

// TOASTS E CONFIRMAÇÃO
// ═══════════════════════════════════════════════════════════
export function mostrarToast(mensagem, tipo = "info") {
  const container = document.getElementById("toast-container")
  const toast = document.createElement("div")
  toast.className = `toast ${tipo}`
  const icone = tipo === "sucesso" ? ICONE_TOAST_SUCESSO : tipo === "erro" ? ICONE_TOAST_ERRO : ""
  toast.innerHTML = `${icone ? `<span class="icone">${icone}</span>` : ""}<span class="texto">${mensagem}</span><button class="fechar" onclick="this.parentElement.remove()" aria-label="${t("perfil.fechar")}">✕</button>`
  container.appendChild(toast)
  const duracao = Math.min(9000, Math.max(4000, mensagem.length * 100))
  setTimeout(() => toast.remove(), duracao)
}

export function confirmarAcao(mensagem, { textoConfirmar, perigo = false } = {}) {
  return new Promise(resolve => {
    document.getElementById("confirm-modal-texto").textContent = mensagem
    const btnConfirmar = document.getElementById("confirm-modal-btn-confirmar")
    const btnCancelar  = document.getElementById("confirm-modal-btn-cancelar")
    btnConfirmar.textContent = textoConfirmar || t("generico.confirmar")
    btnConfirmar.className = perigo ? "btn-danger" : "btn-primary"
    document.getElementById("confirm-modal").classList.add("open")
    function limpar() {
      document.getElementById("confirm-modal").classList.remove("open")
      btnConfirmar.removeEventListener("click", onConfirmar)
      btnCancelar.removeEventListener("click", onCancelar)
    }
    function onConfirmar() { limpar(); resolve(true) }
    function onCancelar()  { limpar(); resolve(false) }
    btnConfirmar.addEventListener("click", onConfirmar)
    btnCancelar.addEventListener("click", onCancelar)
  })
}

// ═══════════════════════════════════════════════════════════
// ESTADOS VAZIOS E SKELETONS
// ═══════════════════════════════════════════════════════════
export function linhasEsqueleto(numColunas, numLinhas = 3) {
  let html = ""
  for (let i = 0; i < numLinhas; i++) {
    html += `<tr class="skeleton-row">${Array.from({ length: numColunas }).map(() =>
      `<td><div class="skeleton-bar" style="width:${60 + Math.random() * 30}%"></div></td>`
    ).join("")}</tr>`
  }
  return html
}
export function linhaVazia(numColunas, titulo, subtitulo, botaoHtml = "") {
  return `<tr><td colspan="${numColunas}"><div class="estado-vazio">${titulo ? `<div class="titulo">${titulo}</div>` : ""}${subtitulo ? `<div class="subtitulo">${subtitulo}</div>` : ""}${botaoHtml}</div></td></tr>`
}
export function mostrarGraficoOuVazio(idCanvas, temDados, mensagem, render) {
  const canvas = document.getElementById(idCanvas)
  const existente = canvas.parentElement.querySelector(".estado-vazio-grafico")
  if (existente) existente.remove()
  if (temDados) {
    canvas.style.display = ""
    render()
  } else {
    canvas.style.display = "none"
    const div = document.createElement("div")
    div.className = "estado-vazio estado-vazio-grafico"
    div.innerHTML = `<div class="subtitulo">${mensagem}</div>`
    canvas.parentElement.appendChild(div)
  }
}

// ═══════════════════════════════════════════════════════════
// VALIDAÇÃO DE FORMULÁRIOS
// ═══════════════════════════════════════════════════════════
export function camposValidos(...ids) {
  for (const id of ids) {
    const el = document.getElementById(id)
    if (!el.checkValidity()) { el.reportValidity(); return false }
  }
  return true
}
export function ligarValidacaoFormulario(idsCampos, idBotao) {
  const botao = document.getElementById(idBotao)
  function atualizar() {
    botao.disabled = !idsCampos.every(id => document.getElementById(id).checkValidity())
  }  
  idsCampos.forEach(id => {
    document.getElementById(id).removeEventListener("input", atualizar)
    document.getElementById(id).addEventListener("input", atualizar)
  })
  atualizar()
}
export function mostrarAjudaAoEscrever(idInput, idAjuda) {
  const input = document.getElementById(idInput)
  const ajuda = document.getElementById(idAjuda)
  input.addEventListener("input", () => { ajuda.style.display = input.value.length > 0 ? "block" : "none" })
}

export function ligarValidacaoMovimento() {
  ligarValidacaoFormulario(["mov-descricao", "mov-valor", "mov-conta-display", "mov-tipo-display", "mov-categoria-display", "mov-data"], "btn-guardar-movimento")
}
// ═══════════════════════════════════════════════════════════
