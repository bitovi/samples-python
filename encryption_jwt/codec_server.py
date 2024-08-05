from functools import partial
from typing import Awaitable, Callable, Iterable, List

from aiohttp import hdrs, web
from google.protobuf import json_format
from temporalio.api.common.v1 import Payload, Payloads

from encryption_jwt.codec import EncryptionCodec

import logging


def build_codec_server() -> web.Application:
    # Cors handler
    async def cors_options(req: web.Request) -> web.Response:
        resp = web.Response()

        logger.info("Received CORS request")
        logger.info(req.headers)
        if req.headers.get(hdrs.ORIGIN) == "http://localhost:8233":
            logger.info("Setting CORS headers for localhost")
            resp.headers[hdrs.ACCESS_CONTROL_ALLOW_ORIGIN] = "http://localhost:8233"

        elif req.headers.get(hdrs.ORIGIN) == "https://cloud.temporal.io":
            logger.info("Setting CORS headers for cloud.temporal.io")
            resp.headers[hdrs.ACCESS_CONTROL_ALLOW_ORIGIN] = "https://cloud.temporal.io"

        # common
        resp.headers[hdrs.ACCESS_CONTROL_ALLOW_METHODS] = "POST"
        resp.headers[hdrs.ACCESS_CONTROL_ALLOW_HEADERS] = "content-type,x-namespace"

        return resp

    # General purpose payloads-to-payloads
    async def apply(
        fn: Callable[[Iterable[Payload]], Awaitable[List[Payload]]], req: web.Request
    ) -> web.Response:
        logger.info("Received request")
        # Read payloads as JSON
        assert req.content_type == "application/json"
        payloads = json_format.Parse(await req.read(), Payloads())

        # Apply
        payloads = Payloads(payloads=await fn(payloads.payloads))

        logger.info("Returning response")
        logger.info(payloads)
        # Apply CORS and return JSON
        resp = await cors_options(req)
        resp.content_type = "application/json"
        resp.text = json_format.MessageToJson(payloads)
        return resp

    # Build app
    codec = EncryptionCodec()
    app = web.Application()
    # set up logger
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    app.add_routes(
        [
            web.post("/encode", partial(apply, codec.encode)),
            web.post("/decode", partial(apply, codec.decode)),
            web.options("/decode", cors_options),
        ]
    )
    return app


if __name__ == "__main__":
    web.run_app(build_codec_server(), host="127.0.0.1", port=8081)
