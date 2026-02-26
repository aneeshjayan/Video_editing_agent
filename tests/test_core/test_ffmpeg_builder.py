import pytest

from core.ffmpeg_builder import FFmpegBuilder


class TestFFmpegBuilder:
    def setup_method(self):
        self.builder = FFmpegBuilder()

    def test_trim_command_structure(self, tmp_dir):
        """Trim command should have correct FFmpeg arguments."""
        cmd = self.builder.trim(
            input_path="input.mp4",
            output_path=f"{tmp_dir}/output.mp4",
            start=5.0,
            end=15.0,
        )
        assert cmd[0] == "ffmpeg"
        assert "-ss" in cmd
        assert "5.0" in cmd
        assert "-to" in cmd
        assert "15.0" in cmd
        assert "-c" in cmd
        assert "copy" in cmd
        assert cmd[-1] == f"{tmp_dir}/output.mp4"

    def test_trim_includes_overwrite_flag(self, tmp_dir):
        """Trim command should include -y to overwrite existing files."""
        cmd = self.builder.trim("in.mp4", f"{tmp_dir}/out.mp4", 0, 10)
        assert "-y" in cmd

    def test_concat_simple_creates_list_file(self, tmp_dir):
        """Concat should create a concat list file."""
        cmd = self.builder.concat_simple(
            input_paths=["a.mp4", "b.mp4"],
            output_path=f"{tmp_dir}/concat.mp4",
        )
        assert "-f" in cmd
        assert "concat" in cmd
        assert "-safe" in cmd

    def test_concat_with_transition_requires_two_inputs(self):
        """Transition concat should fail with fewer than 2 inputs."""
        from core.exceptions import FFmpegError

        with pytest.raises(FFmpegError, match="at least 2"):
            self.builder.concat_with_transition(
                input_paths=["only_one.mp4"],
                output_path="out.mp4",
            )

    def test_change_speed_command(self, tmp_dir):
        """Speed change should set correct filter values."""
        cmd = self.builder.change_speed(
            input_path="input.mp4",
            output_path=f"{tmp_dir}/fast.mp4",
            speed_factor=2.0,
        )
        assert "setpts=0.5*PTS" in " ".join(cmd)
        assert "atempo=2.0" in " ".join(cmd)

    def test_custom_ffmpeg_path(self):
        """Builder should use custom FFmpeg path."""
        builder = FFmpegBuilder(ffmpeg_path="/usr/local/bin/ffmpeg")
        cmd = builder.trim("in.mp4", "out.mp4", 0, 10)
        assert cmd[0] == "/usr/local/bin/ffmpeg"
