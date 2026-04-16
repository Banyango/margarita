import wireup

import margarita.agent.app.cli.writers.logger as logger_writer
import margarita.agent.app.cli.writers.writer as writer
import margarita.agent.app.config as config
from margarita.agent import core, libs

container = wireup.create_async_container(
    injectables=[config, logger_writer, writer, core, libs],
)
