import logging

from celery import chain

from ..celery import app
from . import fs, pdfs, recording, veripy


logger = logging.getLogger(__name__)


@app.task
def debug_task():
    logger.debug('Hello')


@app.task
def log_error(request, exc, traceback):
    logger.error(traceback)


@app.task
def completion(kwargs):
    inputfilepath = kwargs['inputfilepath']
    logger.info(f'Workflow complete for file: {inputfilepath}')
    # TODO: Send email to someplace about completion.


def pipeline(specio_config, inputfilepath):
    """ The Main Workflow for the Specio Pipeline.

    This task dispatches a celery workflow to process the given input config file
    using the given specio configuration. This workflow is broken up into several
    parts, each of which can be run on a separate machine or VM.

    Logs and Errors from each task are logged to the central logging system.

    Usage
    -----

        from run.forrest import tasks
        tasks.pipeline.delay()


    Implementation Notes
    --------------------

    Each of the tasks contained within this workflow are entirely idempotent and
    functional. Some of the tasks do require a file system state, but any required
    state should be provided by the docker volume.

    Any tasks that write to the filesystem automatically clean up after themselves
    leaving the disk in a non-polluted state.

    """
    logger.debug(f'Constructing Specio workflow for: {inputfilepath}')

    kwargs = dict(
        specio_config=specio_config,
        inputfilepath=inputfilepath,
    )

    workflow = chain(
        # Attempt to acquire a lock for the given run
        fs.acquire_lock.si(kwargs),

        # Load in the specio_config
        fs.get_run_config.s(),

        # Do specio_config validation
        fs.validate_run_config.s(),

        # Start the video recording
        recording.start_recording.s(),

        # Run VeriPy
        veripy.veripy.s(),

        # Stop the video recording
        recording.stop_recording.s(),

        # Convert the output of VeriPy to the Specio format
        veripy.convert_to_specio.s(),

        # Get the PDF report
        pdfs.get_report.s(),

        # Copy the recording and the subtitles to the user's preferred destination
        fs.copy_recording.s(),
        fs.copy_subtitles.s(),

        # Write the report to disk
        fs.write_report.s(),

        # Release the lock
        fs.release_lock.s(),

        # Log the completion.
        completion.s(),
    )

    return workflow()
