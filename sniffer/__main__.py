# -*- coding: utf-8 -*-

import click
import asyncio
import logging
import coloredlogs

from .web import start_web_server
from .sniffer import DumpFileLoader, Sniffer


logger = logging.getLogger(__name__)
coloredlogs.install(level="INFO")


@click.command()
@click.option("--device", "-d", default="en0", help="network device you want to sniff at")
@click.option("--dump", type=click.File("wb"), help="dump traffic to this file")
@click.option("--load", type=click.File("rb"), help="traffic dump file to load")
def main(device, dump, load):
    loop = asyncio.get_event_loop()
    futures = []

    if load:
        sniffer = DumpFileLoader(load, loop)
    else:
        sniffer = Sniffer(device, loop, dump=dump)

    futures.append(sniffer.sniff())
    futures.append(start_web_server(loop, sniffer))

    try:
        loop.run_until_complete(asyncio.gather(*futures))
    except KeyboardInterrupt:
        logger.info("Closing....")
        loop.close()


if __name__ == "__main__":
    exit(main())
