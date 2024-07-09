from pathlib import Path
from convert import compile_proto_python
from preprocess import pre_process_proto_dir

if __name__ == '__main__':

    current_dir: Path = Path(__file__).parent.resolve()

    # First run the pre-processor
    pre_process_proto_dir(
        dir_in=current_dir.joinpath("./src").resolve(),
        dir_out=current_dir.joinpath("./dist").resolve()
    )

    # Then run the compiler
    compile_proto_python(
        in_fp=current_dir.joinpath("./dist/webcast.proto").resolve(),
        out_fd=current_dir.parent.parent.joinpath("./TikTokLive/proto"),
        out_fn="tiktok_proto.py"
    )

