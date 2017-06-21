{{ review.timestamp|datetime }}
[{{ app.desc }}]({{ app.name|app_url(review.lang) }}){% if review.version %} (`{{ review.version }}`){% endif %}{% if review.device %} _{{ review.device }}_{% endif %}
{% for rating in range(0, 5) %}{% if review.rating > rating %}★{% else %}☆{% endif %}{% endfor %}
{% if review.title %}*{{ review.title }}*{{ "\n" }}{% endif -%}
```
{{ review.comment }}
```
{% if review.old_rating %}_{% trans %}Changed from{% endtrans %} ({{ review.old_timedelta|timedelta }} {% trans %}ago{% endtrans %}):_
{% for rating in range(0, 5) %}{% if review.old_rating > rating %}★{% else %}☆{% endif %}{% endfor %}
```
{{ review.old_comment }}
```
{% endif %}
{% if dev_id %}{{ review.commentId|review_url(dev_id, app.name) }}{{ "\n" }}{% else %}{% endif %}
