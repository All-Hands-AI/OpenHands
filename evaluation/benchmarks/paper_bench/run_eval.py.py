import chz
from nanoeval.eval import EvalSpec, RunnerArgs
from nanoeval.evaluation import run
from nanoeval.library_config import LibraryConfig
from nanoeval.setup import nanoeval_entrypoint
from paperbench.nano.eval import PaperBench
from paperbench.nano.logging import paperbench_library_config, setup_logging

#uv pip install "git+https://github.com/leandermaben/frontier-evals.git#subdirectory=project/paperbench"


@chz.chz
class DefaultRunnerArgs(RunnerArgs):
    concurrency: int = 5


async def main(
    paperbench: PaperBench,
    runner: DefaultRunnerArgs,
    library_config: LibraryConfig = paperbench_library_config,
) -> None:
    # BREAKPOINT: Entry point: Start of main evaluation function
    breakpoint()
    setup_logging(library_config)
    # BREAKPOINT: After logging setup, before evaluation run
    breakpoint()
    await run(EvalSpec(eval=paperbench, runner=runner))


if __name__ == "__main__":
    nanoeval_entrypoint(chz.entrypoint(main))
