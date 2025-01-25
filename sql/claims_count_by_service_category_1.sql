select
  data_source
, service_category_1
, year(claim_start_date) || lpad(month(claim_start_date),2,0) as year_month
, count(distinct claim_id) as claim_count
from medicare_lds_five_percent.core.medical_claim
group by 1,2,3

union

select 
  data_source
, service_category_1
, year(claim_start_date) || lpad(month(claim_start_date),2,0) as year_month
, count(distinct claim_id) as claim_count
from cms_synthetic.core.medical_claim
group by 1,2,3
order by 1,2,3
