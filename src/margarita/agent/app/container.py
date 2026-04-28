import margarita_open_agent.core as ollama_core
import margarita_open_agent.libs as ollama_libs
import wireup

import margarita.agent.app.cli.writers.logger as logger_writer
import margarita.agent.app.cli.writers.writer as writer
import margarita.agent.app.config as config
from margarita.agent import core, libs

container = wireup.create_async_container(
    injectables=[ollama_core, ollama_libs, config, logger_writer, writer, core, libs],
)
