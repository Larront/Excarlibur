from objects import *
from routines import *
from tools import *


class Excarlibur(GoslingAgent):
    def run(agent):

        # Game Variables
        close = (agent.me.location - agent.ball.location).magnitude() < 2000
        have_boost = agent.me.boost > 20

        # Offside calculation
        my_goal_to_ball, ball_distance = (agent.ball.location - agent.friend_goal.location).normalize(True)
        goal_to_me = agent.me.location - agent.friend_goal.location
        my_distance = my_goal_to_ball.dot(goal_to_me)

        foe_goal_to_ball, foe_ball_distance = (agent.ball.location - agent.foe_goal.location).normalize(True)
        foe_goal_to_foe = agent.foes[0].location - agent.foe_goal.location
        foe_distance = foe_goal_to_ball.dot(foe_goal_to_foe)

        me_onside = my_distance - 200 < ball_distance
        foe_onside = foe_distance - 200 < foe_ball_distance

        # Debug bots on team blue
        if agent.team == 0:
            agent.debug_stack()
            agent.line(agent.friend_goal.location, agent.ball.location, [255, 255, 255])
            onside_marker = agent.friend_goal.location + (my_goal_to_ball * my_distance)
            agent.line(onside_marker - Vector3(0, 0, 100), onside_marker + Vector3(0, 0, 100), [120, 0, 255])

        return_to_goal = False

        # Check if stack is empty
        if len(agent.stack) < 1:
            # Kickoff
            if agent.kickoff_flag:
                agent.push(kickoff())

            # Go for a shot if close and onside, or if onside and opponent is not
            elif (close and me_onside) or (not foe_onside and me_onside):
                # Set up targets
                left_field = Vector3(4200*-side(agent.team), agent.ball.location.y + (1000*-side(agent.team)), 0)
                right_field = Vector3(4200*side(agent.team), agent.ball.location.y + (1000*-side(agent.team)), 0)
                targets = {"goal": (agent.foe_goal.left_post, agent.foe_goal.right_post),
                           "upfield": (left_field, right_field)}

                # Find hits
                shots = find_hits(agent, targets)
                if len(shots["goal"]) > 0:
                    agent.push(shots["goal"][0])
                # Else shoot upfield if ball is not upfield
                elif len(shots["upfield"]) > 0 and abs(agent.friend_goal.location.y - agent.ball.location.y) < 8490:
                    agent.push(shots["upfield"][0])
                else:
                    return_to_goal = True

            elif not me_onside and not have_boost:
                boosts = [boost for boost in agent.boosts if boost.large and boost.active and abs(
                    agent.friend_goal.location.y - boost.location.y) - 200 < abs(agent.friend_goal.location.y - agent.me.location.y)]
                if len(boosts) > 0:
                    closest = boosts[0]
                    for boost in boosts:
                        if (boost.location - agent.me.location).magnitude() < (closest.location - agent.me.location).magnitude():
                            closest = boost
                    agent.push(goto_boost(closest, agent.friend_goal.location))
                else:
                    return_to_goal = True
            else:
                agent.push(short_shot(agent.foe_goal.location))

        if return_to_goal:
            relative_target = agent.friend_goal.location - agent.me.location
            angles = defaultPD(agent, agent.me.local(relative_target))
            defaultThrottle(agent, 2300)
            agent.controller.boost = False if abs(angles[1]) > 0.5 or agent.me.airborne else True
            agent.controller.handbrake = True if abs(angles[1]) > 2.8 else False
