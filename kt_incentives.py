from config_kt import *

#Round to 6 decimals
ROUNDTODIGITS = 6

def update_incentives_allocation_dynamic_state(yield_token_supply: int, principal_token_supply: int, lp_token_supply: int, pt_in_pt_lp: int, yield_token_allocation: float, pt_lp_ratio: float, refracted_lp_ratio: float):
    new_refracted_lp_ratio = round(yield_token_supply / lp_token_supply, ROUNDTODIGITS)
    new_pt_lp_ratio = round(pt_in_pt_lp / principal_token_supply, ROUNDTODIGITS)

    if refracted_lp_ratio == 0 or (new_refracted_lp_ratio / refracted_lp_ratio) < REFRACTED_LP_RATIO_DELTA_LOWER_BOUND:
        yield_token_allocation = round(yield_token_allocation + min(YIELD_TOKEN_ALLOCATION_MAX - yield_token_allocation, YIELD_TOKEN_ALLOCATION_INCREASE_STEP_SIZE), ROUNDTODIGITS)
    elif pt_lp_ratio == 0 or (new_pt_lp_ratio / pt_lp_ratio) < PT_LP_RATIO_DELTA_LOWER_BOUND:
        yield_token_allocation = round(yield_token_allocation - min(yield_token_allocation - YIELD_TOKEN_ALLOCATION_MIN, YIELD_TOKEN_ALLOCATION_DECREASE_STEP_SIZE), ROUNDTODIGITS)
    #Update state
    pt_lp_ratio = new_pt_lp_ratio
    refracted_lp_ratio = new_refracted_lp_ratio
    return yield_token_allocation, pt_lp_ratio, refracted_lp_ratio

#state
yield_token_allocation = 0.15
pt_lp_ratio = 0.75 # previous epoch pt_in_pt_lp / previous epoch principal_token_supply
refracted_lp_ratio = 0.6 # previous epoch yield_token_supply / previous epoch lp_token_supply

updated_values = update_incentives_allocation_dynamic_state(1000, 1000, 2000, 800, yield_token_allocation, pt_lp_ratio, refracted_lp_ratio)
yield_token_allocation = updated_values[0]
pt_lp_ratio = updated_values[1]
refracted_lp_ratio = updated_values[2]

print("yield token allocation: {0}, pt_lp_ratio: {1}, refracted_lp_ratio: {2}".format(yield_token_allocation, pt_lp_ratio, refracted_lp_ratio))

# #######################################
updated_values = update_incentives_allocation_dynamic_state(2000, 3000, 12000, 2500, yield_token_allocation, pt_lp_ratio, refracted_lp_ratio)
yield_token_allocation = updated_values[0]
pt_lp_ratio = updated_values[1]
refracted_lp_ratio = updated_values[2]

print("yield token allocation: {0}, pt_lp_ratio: {1}, refracted_lp_ratio: {2}".format(yield_token_allocation, pt_lp_ratio, refracted_lp_ratio))

# #######################################
updated_values = update_incentives_allocation_dynamic_state(11000, 11500, 12000, 2500, yield_token_allocation, pt_lp_ratio, refracted_lp_ratio)
yield_token_allocation = updated_values[0]
pt_lp_ratio = updated_values[1]
refracted_lp_ratio = updated_values[2]

print("yield token allocation: {0}, pt_lp_ratio: {1}, refracted_lp_ratio: {2}".format(yield_token_allocation, pt_lp_ratio, refracted_lp_ratio))