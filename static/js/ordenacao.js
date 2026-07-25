import { renderizarTabelaRecorrentes } from './analise.js'
import { renderizarTabelaContas } from './contas.js'
import { ICONE_CHECK, ICONE_ORDENAR_ASC, ICONE_ORDENAR_DESC, ICONE_ORDENAR_NEUTRO, estadoGlobal } from './estado.js'
import { fecharTodosOsFiltros } from './filtros.js'
import { t } from './i18n.js'
import { renderizarTabelaMovimentos } from './movimentos.js'

// ORDENAÇÃO DE TABELAS
// ═══════════════════════════════════════════════════════════
export function atualizarIconesOrdenacao(idCabecalho, ordenacao) {
  document.querySelectorAll(`#${idCabecalho} th[data-campo]`).forEach(th => {
    const icone = th.querySelector(".icone-ordenacao")
    if (!icone) return
    if (th.dataset.campo === ordenacao.campo) {
      th.classList.add("ordenado")
      th.setAttribute("aria-sort", ordenacao.direcao === 1 ? "ascending" : "descending")
      icone.innerHTML = ordenacao.direcao === 1 ? ICONE_ORDENAR_ASC : ICONE_ORDENAR_DESC
    } else {
      th.classList.remove("ordenado")
      th.setAttribute("aria-sort", "none")
      icone.innerHTML = ICONE_ORDENAR_NEUTRO
    }
  })
}

// ═══════════════════════════════════════════════════════════
// Funções (não consts) porque os rótulos vêm de t() — um const calculado uma vez só no
// arranque do módulo ficaria com o texto da língua inicial mesmo depois de o utilizador
// mudar de língua a meio da sessão sem recarregar a página.
const opcoesOrdenarContas = () => ({
  nome:   { rotulo: t("ordenar.nome"),        direcoes: [{ valor: 1, rotulo: t("ordenar.a_z") }, { valor: -1, rotulo: t("ordenar.z_a") }] },
  saldo:  { rotulo: t("ordenar.saldo_atual"), direcoes: [{ valor: -1, rotulo: t("ordenar.maior_menor") }, { valor: 1, rotulo: t("ordenar.menor_maior") }] },
  inicio: { rotulo: t("ordenar.data_inicio"), direcoes: [{ valor: 1, rotulo: t("ordenar.antigo_recente") }, { valor: -1, rotulo: t("ordenar.recente_antigo") }] },
})
// renderizarPainelOrdenarCt/Mov/Recorrentes + selecionarCampo/Direcao + toggle/fechar
// (15 funções, 3 quase idênticas cada) foram consolidadas numa só implementação
// parametrizada — ver PREFIXOS_ORDENAR, logo a seguir a opcoesOrdenarRecorrentes.

const opcoesOrdenarMovimentos = () => ({
  data:      { rotulo: t("ordenar.data"),      direcoes: [{ valor: -1, rotulo: t("ordenar.recente_antigo") }, { valor: 1, rotulo: t("ordenar.antigo_recente") }] },
  valor:     { rotulo: t("ordenar.valor"),     direcoes: [{ valor: -1, rotulo: t("ordenar.maior_menor") }, { valor: 1, rotulo: t("ordenar.menor_maior") }] },
  descricao: { rotulo: t("ordenar.descricao"), direcoes: [{ valor: 1, rotulo: t("ordenar.a_z") }, { valor: -1, rotulo: t("ordenar.z_a") }] },
})
// (ver nota acima de opcoesOrdenarContas — mesma consolidação)

const opcoesOrdenarRecorrentes = () => ({
  valor_medio:           { rotulo: t("ordenar.valor_medio"),   direcoes: [{ valor: -1, rotulo: t("ordenar.maior_menor") }, { valor: 1, rotulo: t("ordenar.menor_maior") }] },
  intervalo_medio_dias:  { rotulo: t("ordenar.frequencia"),    direcoes: [{ valor: 1, rotulo: t("ordenar.frequente_raro") }, { valor: -1, rotulo: t("ordenar.raro_frequente") }] },
  proxima_data_estimada: { rotulo: t("ordenar.proxima_data"),  direcoes: [{ valor: 1, rotulo: t("ordenar.proximo_distante") }, { valor: -1, rotulo: t("ordenar.distante_proximo") }] },
})
// Painel de "Ordenar" — Contas/Movimentos/Recorrentes tinham cada um a sua cópia quase
// idêntica (renderizar painel, escolher campo, escolher direcção, abrir/fechar). Uma só
// implementação parametrizada por prefixo ("ct" | "mov" | "an-recorrentes"), que já
// coincide com os prefixos usados nos ids do HTML (ct-ordenar-btn, mov-ordenar-panel, etc).
const PREFIXOS_ORDENAR = {
  ct: {
    opcoes: opcoesOrdenarContas, padrao: "nome",
    obterEstado: () => estadoGlobal.ordenacaoContas,
    definirEstado: novo => { estadoGlobal.ordenacaoContas = novo },
    renderizarTabela: () => renderizarTabelaContas(),
  },
  mov: {
    opcoes: opcoesOrdenarMovimentos, padrao: "data",
    obterEstado: () => estadoGlobal.ordenacaoMovimentos,
    definirEstado: novo => { estadoGlobal.ordenacaoMovimentos = novo },
    renderizarTabela: () => renderizarTabelaMovimentos(),
  },
  "an-recorrentes": {
    opcoes: opcoesOrdenarRecorrentes, padrao: "valor_medio",
    obterEstado: () => estadoGlobal.ordenacaoRecorrentes,
    definirEstado: novo => { estadoGlobal.ordenacaoRecorrentes = novo },
    renderizarTabela: () => renderizarTabelaRecorrentes(),
  },
}
export function renderizarPainelOrdenar(prefixo) {
  const { opcoes: obterOpcoes, padrao, obterEstado } = PREFIXOS_ORDENAR[prefixo]
  const opcoes = obterOpcoes()
  const ordenacaoAtual = obterEstado()
  document.getElementById(`${prefixo}-ordenar-campos`).innerHTML = Object.entries(opcoes).map(([chave, o]) =>
    `<div class="filtro-item-linha${ordenacaoAtual.campo === chave ? ' selecionado' : ''}" onclick="selecionarCampoOrdenar('${prefixo}', '${chave}')"><span>${o.rotulo}</span><span class="check">${ICONE_CHECK}</span></div>`
  ).join("")
  const direcoes = opcoes[ordenacaoAtual.campo]?.direcoes || opcoes[padrao].direcoes
  document.getElementById(`${prefixo}-ordenar-direcoes`).innerHTML = direcoes.map(d =>
    `<div class="filtro-item-linha${ordenacaoAtual.direcao === d.valor ? ' selecionado' : ''}" onclick="selecionarDirecaoOrdenar('${prefixo}', ${d.valor})"><span>${d.rotulo}</span><span class="check">${ICONE_CHECK}</span></div>`
  ).join("")
  document.getElementById(`${prefixo}-ordenar-btn-texto`).textContent = t("ordenar.prefixo_botao") + (opcoes[ordenacaoAtual.campo]?.rotulo || opcoes[padrao].rotulo)
}
export function selecionarCampoOrdenar(prefixo, campo) {
  const cfg = PREFIXOS_ORDENAR[prefixo]
  cfg.definirEstado({ campo, direcao: cfg.opcoes()[campo].direcoes[0].valor })
  renderizarPainelOrdenar(prefixo)
  cfg.renderizarTabela()
}
export function selecionarDirecaoOrdenar(prefixo, direcao) {
  const cfg = PREFIXOS_ORDENAR[prefixo]
  cfg.obterEstado().direcao = direcao
  renderizarPainelOrdenar(prefixo)
  cfg.renderizarTabela()
}
export function toggleOrdenar(prefixo, e) {
  e.stopPropagation()
  const painel = document.getElementById(`${prefixo}-ordenar-panel`)
  const estavaAberto = painel.classList.contains("aberto")
  fecharTodosOsFiltros()
  painel.classList.toggle("aberto", !estavaAberto)
}
export function fecharOrdenar(prefixo) {
  document.getElementById(`${prefixo}-ordenar-panel`).classList.remove("aberto")
}


// ═══════════════════════════════════════════════════════════
