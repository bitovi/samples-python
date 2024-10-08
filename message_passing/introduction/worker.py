import asyncio
import logging

from temporalio.client import Client
from temporalio.worker import Worker

from message_passing.introduction import TASK_QUEUE
from message_passing.introduction.activities import call_greeting_service
from message_passing.introduction.workflows import GreetingWorkflow

interrupt_event = asyncio.Event()


async def main():
    logging.basicConfig(level=logging.INFO)

    client = await Client.connect("localhost:7233")

    async with Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[GreetingWorkflow],
        activities=[call_greeting_service],
    ):
        logging.info("Worker started, ctrl+c to exit")
        await interrupt_event.wait()
        logging.info("Shutting down")


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        interrupt_event.set()
        loop.run_until_complete(loop.shutdown_asyncgens())
