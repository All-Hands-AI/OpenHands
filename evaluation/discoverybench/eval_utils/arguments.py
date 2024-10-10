import argparse


class Arguments(argparse.ArgumentParser):
    def __init__(self, groups=None):
        super().__init__(conflict_handler='resolve')
        # Common flags
        self.add_argument('--out_dir', type=str, default='outputs')
        self.add_argument(
            '--debug', action=argparse.BooleanOptionalAction, default=False
        )
        self.add_argument(
            '--verbose', action=argparse.BooleanOptionalAction, default=False
        )
        self.add_argument('--seed', type=int, default=17)
        self.add_argument('--run_id', type=str)

        if not isinstance(
            groups, list
        ):  # COMMENT: changed from type check to isinstance
            groups = [groups]

        for group in groups:
            if group == 'eval':
                self.add_argument('--in_dir', type=str)
                self.add_argument(
                    '--save', action=argparse.BooleanOptionalAction, default=True
                )
            elif group == 'generate':
                self.add_argument('--n_instances', type=int, default=None)
                self.add_argument(
                    '--save', action=argparse.BooleanOptionalAction, default=False
                )
                self.add_argument(
                    '--inject_semantics',
                    action=argparse.BooleanOptionalAction,
                    default=False,
                )
                self.add_argument('--topics_fpath', type=str)
                self.add_argument(
                    '--openai_topic_model', type=str, default='gpt-3.5-turbo'
                )
                self.add_argument('--n_topics', type=int, default=50)
                self.add_argument(
                    '--openai_interp_model', type=str, default='gpt-3.5-turbo'
                )
                self.add_argument('--max_generation_retries', type=int, default=3)
                self.add_argument(
                    '--sample_unique_topics',
                    action=argparse.BooleanOptionalAction,
                    default=True,
                )
                self.add_argument('--test_set_prop', type=float, default=0.4)
                self.add_argument(
                    '--eval_gold', action=argparse.BooleanOptionalAction, default=True
                )
                self.add_argument(
                    '--skip_on_error',
                    action=argparse.BooleanOptionalAction,
                    default=False,
                )
                self.add_argument(
                    '--datasets', action=argparse.BooleanOptionalAction, default=False
                )
                self.add_argument('--semantics_fpath', type=str)
                self.add_argument('--datasets_fpath', type=str)
                self.add_argument(
                    '--openai_semantics_model', type=str, default='gpt-3.5-turbo'
                )
                self.add_argument(
                    '--openai_datasets_model', type=str, default='gpt-3.5-turbo'
                )
                self.add_argument(
                    '--openai_query_model', type=str, default='gpt-3.5-turbo'
                )
                self.add_argument('--n_rows', type=int, default=500)
                self.add_argument('--semantic_depth', type=int, default=3)
                self.add_argument('--leaf_prob', type=float, default=0.4)
                self.add_argument(
                    '--benchmark', action=argparse.BooleanOptionalAction, default=False
                )
