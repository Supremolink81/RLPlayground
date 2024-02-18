import torch
import gymnasium
import random
from typing import Optional, Callable
from doom_rl.reinforcement_learning.algorithms.base_classes import *
from doom_rl.reinforcement_learning.algorithms.dqn.loss import loss_function

class DQN(SingleAgentRLPipeline):

    """
    Implementation of Deep Q Learning. Uses the optimal action

    from the Q function in order to take actions.

    Original Paper: Playing Atari with Deep Reinforcement
     
    Learning by Mnih et al, https://arxiv.org/pdf/1312.5602.pdf

    Fields:

        `gymnasium.Env` environment: the environment the agent resides in.

        `torch.nn.Module` q_function: the Q function.
    """

    q_function: torch.nn.Module

    def __init__(self, environment: gymnasium.Env, q_function_architecture: torch.nn.Module):

        super().__init__(environment)

        self.q_function = q_function_architecture

    def epsilon_greedy_action(self, state: ArrayType, epsilon: float) -> int:

        random_number: float = random.random()

        if random_number >= epsilon:

            return self.environment.action_space.sample()

        else:

            with torch.no_grad():

                action_distribution: torch.Tensor = self.q_function(state.reshape((1,)+state.shape))

                return torch.argmax(action_distribution)[0]
    
    def train(self, **kwargs: Dict[str, Any]) -> None:

        buffer: ReplayBuffer = ReplayBuffer(kwargs["replay_buffer_capacity"])

        optimizer: torch.optim.Optimizer = kwargs["optimizer"]

        episodes: int = kwargs["episodes"]

        discount_factor: float = kwargs["discount_factor"]

        epsilon: float = kwargs["epsilon"]

        batch_size: int = kwargs["batch_size"]

        state_transform: Optional[Callable[[torch.Tensor], torch.Tensor]] = kwargs.get("state_transform", None)

        for _ in range(episodes):

            terminated: bool = False

            truncated: bool = False

            current_state: torch.Tensor = torch.as_tensor(self.environment.reset()[0])

            if state_transform:

                current_state = state_transform(current_state)

            while not terminated and not truncated:

                action: int = self.epsilon_greedy_action(current_state, epsilon)

                next_state, reward, terminated, truncated, _ = self.environment.step(action)

                next_state = torch.as_tensor(next_state)

                if state_transform:

                    next_state = state_transform(next_state)

                non_terminal_state: int = not terminated and not truncated

                buffer.add((current_state, reward, action, next_state, non_terminal_state))

                optimizer.zero_grad()

                batch: list[Transition] = buffer.sample(batch_size)

                loss: torch.Tensor = loss_function(self.q_function, batch, discount_factor)

                loss.backward()

                optimizer.step()

                current_state = next_state.clone()

            self.environment.reset()

    def run(self, episodes: int = -1) -> None:

        episode: int = 0

        while episode < episodes:



            self.environment.render("human")