import logging

logger = logging.getLogger(__name__)


def notificar_pedido_criado(pedido_id, usuario_id):
    logger.info("Enviando e-mail: pedido %s criado para usuario %s", pedido_id, usuario_id)
    logger.info("Enviando SMS: seu pedido foi recebido!")
    logger.info("Enviando push: novo pedido recebido pelo sistema")


def notificar_mudanca_status(pedido_id, novo_status):
    if novo_status == "aprovado":
        logger.info("Notificação: pedido %s foi aprovado! Preparar envio.", pedido_id)
    elif novo_status == "cancelado":
        logger.info("Notificação: pedido %s cancelado. Devolver estoque.", pedido_id)
