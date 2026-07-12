/**
 * Função para filtrar as linhas da tabela pelo status
 * @param {string} status - O status desejado ou 'todos' para limpar o filtro
 */
function filtrarStatus(status) {
  const linhas = document.querySelectorAll('.linha-os');

  linhas.forEach(linha => {
    const statusLinha = linha.getAttribute('data-status');

    if (status === 'todos') {
      linha.style.display = '';
    } else {
      linha.style.display = (statusLinha === status) ? '' : 'none';
    }
  });
}

/**
 * Função para abrir o modal de detalhes e adicionar botão de finalizar se necessário
 * @param {string} id - ID da Ordem de Serviço
 * @param {string} cliente - Nome do cliente
 * @param {string} status - Status da OS
 * @param {string} placa - Placa do veículo
 */
function abrirDetalhes(id, cliente, status, placa) {
  const conteudo = document.getElementById('conteudoModal');

  // Verifica se o status permite finalizar
  let botaoFinalizar = '';
  if (status === 'Em Execução') {
    // Busca o token CSRF que deve estar no seu HTML
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    botaoFinalizar = `
            <hr>
            <form action="/clientes/finalizar-os/${id}/" method="POST">
                <input type="hidden" name="csrfmiddlewaretoken" value="${csrfToken}">
                <button type="submit" class="btn btn-success w-100">Finalizar OS</button>
            </form>
        `;
  }

  // Injeta os dados e o botão condicional no corpo do modal
  conteudo.innerHTML = `
        <p><strong>ID OS:</strong> ${id}</p>
        <p><strong>Cliente:</strong> ${cliente}</p>
        <p><strong>Status:</strong> ${status}</p>
        <p><strong>Veículo:</strong> ${placa}</p>
        ${botaoFinalizar}
    `;

  // Inicializa e exibe o modal do Bootstrap
  var myModal = new bootstrap.Modal(document.getElementById('modalDetalhes'));
  myModal.show();
}