select has_relic.*, reward.base, reward.rarity
from has_relic
inner join relic
    on has_relic.era == relic.era
    and has_relic.minor == relic.minor
inner join reward
	on has_relic.era == reward.era
	and has_relic.minor == reward.minor 
where
    has_relic.player == "sooby"
	and reward.base == "Forma"
	and relic.vaulted == 0
order by reward.rarity asc, has_relic.quantity desc;