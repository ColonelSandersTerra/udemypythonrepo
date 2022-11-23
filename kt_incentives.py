from config_kt import *

def update_incentives_allocation_dynamic_state(yield_token_supply: int, principal_token_supply: int, lp_token_supply: int, pt_in_pt_lp: int, yield_token_allocation: float, pt_lp_ratio: float, refracted_lp_ratio: float):
    new_refracted_lp_ratio = yield_token_supply / lp_token_supply
    new_pt_lp_ratio = pt_in_pt_lp / principal_token_supply

    if refracted_lp_ratio == 0 or (new_refracted_lp_ratio / refracted_lp_ratio) < REFRACTED_LP_RATIO_DELTA_LOWER_BOUND:
        yield_token_allocation += min(YIELD_TOKEN_ALLOCATION_MAX - yield_token_allocation, YIELD_TOKEN_ALLOCATION_INCREASE_STEP_SIZE)
    elif pt_lp_ratio == 0 or (new_pt_lp_ratio / pt_lp_ratio) < PT_LP_RATIO_DELTA_LOWER_BOUND:
        yield_token_allocation -= min(yield_token_allocation - YIELD_TOKEN_ALLOCATION_MIN, YIELD_TOKEN_ALLOCATION_DECREASE_STEP_SIZE)
    #Update state
    pt_lp_ratio = new_pt_lp_ratio
    refracted_lp_ratio = new_refracted_lp_ratio
    return yield_token_allocation

#state
pt_lp_ratio = 0.75 # previous epoch pt_in_pt_lp / previous epoch principal_token_supply
refracted_lp_ratio = 0.6 # previous epoch yield_token_supply / previous epoch lp_token_supply
yield_token_allocation = 0.15

yield_token_allocation = update_incentives_allocation_dynamic_state(1000, 1000, 2000, 800, yield_token_allocation, pt_lp_ratio, refracted_lp_ratio)
print("yield token allocation: {0}".format(yield_token_allocation))
print("pt_lp_ratio: {0}".format(pt_lp_ratio))
print("refracted_lp_ratio: {0}".format(refracted_lp_ratio))