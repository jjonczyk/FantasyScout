from flask import Flask, render_template

from data_processing.constants import FINAL_VIEW_COLUMNS
from fantasy_scout import FantasyScout

app = Flask(__name__)

@app.route('/')
def return_dataframe():
    scout = FantasyScout()
    scout.my_team = FantasyScout.select_team()
    scout.my_team = FantasyScout.calc_fixtures(scout.my_team)
    scout.my_team = FantasyScout.add_comments(scout.my_team)
    final_df = scout.my_team[FINAL_VIEW_COLUMNS]

    # Convert DataFrame to HTML w/ Bootstrap
    table_html = final_df.to_html(classes='table table-striped', index=False)
    return render_template('table.html', table=table_html)


if __name__ == '__main__':
    app.run(debug=True)
