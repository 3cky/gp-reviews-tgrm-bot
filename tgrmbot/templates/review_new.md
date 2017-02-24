{{ review.timestampMsec|datetime }}
[{{ app.desc }}]({{ app.name|app_url(gp_lang) }}){% if review.documentVersion %} (`{{ review.documentVersion }}`){% endif %}{% if review.deviceName %} /{{ review.deviceName }}/{% endif %}
{% for rating in range(0, 5) %}{% if review.starRating > rating %}★{% else %}☆{% endif %}{% endfor %}
{% if review.title %}*{{ review.title }}*{{ "\n" }}{% endif %}```
{{ review.comment }}
```
{% if dev_id %}{{ review.commentId|review_url(dev_id, app.name) }}{{ "\n" }}{% else %}{% endif %}
