import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pickle
import plotly.express as px
import requests
import json

from pathlib import Path

script_location = Path(__file__).absolute().parent

def radar_chart(client, param):
    """Fonction qui trace le graphe radar du client comparé aux crédits accordés/refusés
    pour un certain paramètre"""

    def _invert(x, limits):
        """inverts a value x on a scale from
        limits[0] to limits[1]"""
        return limits[1] - (x - limits[0])

    def _scale_data(data, ranges):
        """scales data[1:] to ranges[0],
        inverts if the scale is reversed"""
        for d, (y1, y2) in zip(data, ranges):
            assert (y1 <= d <= y2) or (y2 <= d <= y1)

        x1, x2 = ranges[0]
        d = data[0]

        if x1 > x2:
            d = _invert(d, (x1, x2))
            x1, x2 = x2, x1

        sdata = [d]

        for d, (y1, y2) in zip(data[1:], ranges[1:]):
            if y1 > y2:
                d = _invert(d, (y1, y2))
                y1, y2 = y2, y1

            sdata.append((d - y1) / (y2 - y1) * (x2 - x1) + x1)

        return sdata

    class ComplexRadar():
        def __init__(self, fig, variables, ranges,
                     n_ordinate_levels=6):
            angles = np.arange(0, 360, (360. / len(variables)))

            axes = [fig.add_axes([0.1, 0.1, 0.9, 0.9], polar=True,
                                 label="axes{}".format(i))
                    for i in range(len(variables))]

            axes[0].set_thetagrids(angles, labels=[])

            for ax in axes[1:]:
                ax.patch.set_visible(False)
                ax.grid("off")
                ax.xaxis.set_visible(False)

            for i, ax in enumerate(axes):
                grid = np.linspace(*ranges[i],
                                   num=n_ordinate_levels)
                gridlabel = ["{}".format(round(x, 2))
                             for x in grid]
                if ranges[i][0] > ranges[i][1]:
                    grid = grid[::-1]  # hack to invert grid
                    # gridlabels aren't reversed
                gridlabel[0] = ""  # clean up origin
                ax.set_rgrids(grid, labels=gridlabel, angle=angles[i])
                # ax.spines["polar"].set_visible(False)
                ax.set_ylim(*ranges[i])

            ticks = angles
            ax.set_xticks(np.deg2rad(ticks))  # crée les axes suivant les angles, en radians
            ticklabels = variables
            ax.set_xticklabels(ticklabels, fontsize=10)  # définit les labels

            angles1 = np.linspace(0, 2 * np.pi, len(ax.get_xticklabels()) + 1)
            angles1[np.cos(angles1) < 0] = angles1[np.cos(angles1) < 0] + np.pi
            angles1 = np.rad2deg(angles1)
            labels = []
            for label, angle in zip(ax.get_xticklabels(), angles1):
                x, y = label.get_position()
                lab = ax.text(x, y - .5, label.get_text(), transform=label.get_transform(),
                              ha=label.get_ha(), va=label.get_va())
                lab.set_rotation(angle)
                lab.set_fontsize(16)
                lab.set_fontweight('bold')
                labels.append(lab)
            ax.set_xticklabels([])

            # variables for plotting
            self.angle = np.deg2rad(np.r_[angles, angles[0]])
            self.ranges = ranges
            self.ax = axes[0]

        def plot(self, data, *args, **kw):
            sdata = _scale_data(data, self.ranges)
            self.ax.plot(self.angle, np.r_[sdata, sdata[0]], *args, **kw)

        def fill(self, data, *args, **kw):
            sdata = _scale_data(data, self.ranges)
            self.ax.fill(self.angle, np.r_[sdata, sdata[0]], *args, **kw)

    def ok_impayes(df, var_name):
        cat = df_group[df_group['SK_ID_CURR'] == identifiant][var_name].iloc[0]
        ok = df[df[var_name] == cat][df['TARGET'] == 0]
        ok.drop(['TARGET', var_name], inplace=True, axis=1)
        impayes = df[df[var_name] == cat][df['TARGET'] == 1]
        impayes.drop(['TARGET', var_name], inplace=True, axis=1)
        return ok, impayes, cat

    if param == 'Genre':
        df = genre.copy()
        ok, impayes, cat = ok_impayes(df, 'CODE_GENDER')
        client = pd.concat([client, ok, impayes], ignore_index=True)

    if param == "Type d'entreprise":
        df = organization_type.copy()
        ok, impayes, cat = ok_impayes(df, 'ORGANIZATION_TYPE')
        client = pd.concat([client, ok, impayes], ignore_index=True)

    if param == "Niveau d'éducation":
        df = education_type.copy()
        ok, impayes, cat = ok_impayes(df, 'NAME_EDUCATION_TYPE')
        client = pd.concat([client, ok, impayes], ignore_index=True)

    if param == "Niveau de revenus":
        df = income.copy()
        ok, impayes, cat = ok_impayes(df, 'AMT_INCOME')
        client = pd.concat([client, ok, impayes], ignore_index=True)

    if param == 'Statut marital':
        df = family.copy()
        ok, impayes, cat = ok_impayes(df, 'NAME_FAMILY_STATUS')
        client = pd.concat([client, ok, impayes], ignore_index=True)

    # data
    variables = ("Durée emprunt", "Annuités", "Âge",
                 "Début contrat travail", "Annuités/revenus")
    data_ex = client.iloc[0]
    ranges = [(min(client["Durée emprunt"]) - 5, max(client["Durée emprunt"]) + 1),
              (min(client["Annuités"]) - 5000, max(client["Annuités"]) + 5000),
              (min(client["Âge"]) - 5, max(client["Âge"]) + 5),
              (min(client["Début contrat travail"]) - 1, max(client["Début contrat travail"]) + 1),
              (min(client["Annuités/revenus"]) - 5, max(client["Annuités/revenus"]) + 5)]
    # plotting
    fig1 = plt.figure(figsize=(6, 6))
    radar = ComplexRadar(fig1, variables, ranges)
    radar.plot(data_ex, label='Notre client')
    radar.fill(data_ex, alpha=0.2)

    radar.plot(ok.iloc[0],
               label='Moyenne des clients similaires sans défaut de paiement',
               color='g')
    radar.plot(impayes.iloc[0],
               label='Moyenne des clients similaires avec défaut de paiement',
               color='r')

    fig1.legend(bbox_to_anchor=(1.7, 1))

    st.pyplot(fig1)


def bar_plot(df, col):
    labels = {'CODE_GENDER': 'Genre',
              'ORGANIZATION_TYPE': "Type d'entreprise",
              'NAME_EDUCATION_TYPE': "Niveau d'éducation",
              'AMT_INCOME': "Niveau de revenus",
              'NAME_FAMILY_STATUS': 'Statut marital',
              'Count': 'Effectif'}
    titre = f"Répartition du nombre et du pourcentage d'impayés suivant le {str.lower(labels[col])}"
    fig = px.bar(df, x=col, y="Count",
                 color="Cible", text="Percentage",
                 labels=labels,
                 color_discrete_sequence=['#90ee90', '#ff4500'],
                 title=titre
                 )
    st.plotly_chart(fig)


st.set_page_config(layout='wide',
                   page_title="Dashboard interactif : décision d'octroi de crédit")
st.write("""
# Dashboard interactif : décision d'octroi de crédit
Dashboard interactif à destination des gestionnaires de la relation client 
permettant d'interpréter les prédictions faites par le modèle et d’améliorer 
la connaissance client des chargés de relation client.
""")

col1, col2, col3 = st.columns([5,1,10]) # crée 3 colonnes
with col1:
    st.write("### Merci d'entrer un identifiant client :")
    identifiant = st.number_input(' ', min_value=100001, max_value=112188)

with st.spinner('Import des données'):
    df = pd.read_csv("source/data_api.csv")

    df_int = pd.read_csv('source/df_interprete')
    df_int.drop('Unnamed: 0', axis=1, inplace=True)

    df_group = pd.read_csv('source/df_group')

    df_int_sans_unite = pd.read_csv('source/df_interp_sans_unite')

    genre = pd.read_csv('source/genre')
    income = pd.read_csv('source/income')
    education_type = pd.read_csv('source/education_type')
    organization_type = pd.read_csv('source/organization_type')
    family = pd.read_csv('source/family')


interpretable_important_data = ['SK_ID_CURR',
                                'PAYMENT_RATE',
                                'AMT_ANNUITY',
                                'DAYS_BIRTH',
                                'DAYS_EMPLOYED',
                                'ANNUITY_INCOME_PERC']

interpretable_important_data_target = ['SK_ID_CURR',
                                       'PAYMENT_RATE',
                                       'AMT_ANNUITY',
                                       'DAYS_BIRTH',
                                       'DAYS_EMPLOYED',
                                       'ANNUITY_INCOME_PERC',
                                       'TARGET']

with st.spinner('Import des modèles'):
    # import du modèle lgbm entrainé
    infile = open('source/LightGBMModel.pkl', 'rb')
    lgbm = pickle.load(infile)
    infile.close()

    # import du modèle NearestNeighbors entrainé sur le trainset
    infile = open('source/NearestNeighborsModel.pkl', 'rb')
    nn = pickle.load(infile)
    infile.close()

    # import du dataframe nettoyé pour le NearestNeighbors
    df_nn = pd.read_csv('source/df_nn')
    

    # import du Standard Scaler entrainé pour le NearestNeighbors
    infile = open('source/StandardScaler.pkl', 'rb')
    std = pickle.load(infile)
    infile.close()

with st.spinner('Calcul en cours'):
    if (df['SK_ID_CURR'] == identifiant).sum() == 0:
        st.write("Identifiant client inconnu")
    else:
        df_tmp = pd.read_csv("source/data_api.csv")
        df_client = df[df['SK_ID_CURR'] == identifiant]
        df_proba = df_tmp[interpretable_important_data_target]
        df_proba_client = df_proba[df_proba['SK_ID_CURR'] == identifiant]

        df_client_int = df_int[df_int['Identifiant'] == identifiant]
        df_client_int_SU = df_int_sans_unite[df_int_sans_unite['Identifiant'] == identifiant]
        df_client_int.set_index('Identifiant', inplace=True)
        # on affiche notre client
        with col3:
            st.write('## Informations client',
                     df_client_int.drop('Défaut paiement', axis=1))

        with col1:
            feats = [f for f in df_client.columns if f not in ['SK_ID_CURR', 'TARGET']]
            
            # Post request
            url = 'https://bank-projet7.herokuapp.com/predictUnpaid'
            
            myobj = {
                "PAYMENT_RATE": df_proba_client["PAYMENT_RATE"].iloc[0],
                "AMT_ANNUITY": df_proba_client["AMT_ANNUITY"].iloc[0],
                "DAYS_BIRTH": int(df_proba_client["DAYS_BIRTH"].iloc[0]),
                "DAYS_EMPLOYED": df_proba_client["DAYS_EMPLOYED"].iloc[0],
                "ANNUITY_INCOME_PERC": df_proba_client["ANNUITY_INCOME_PERC"].iloc[0]
            }
            myobj
            x = requests.post(url, json = myobj)

            #Create the pandas DataFrame
            json_object = json.loads(x.text)
            data = [['tom', json_object["prediction"]]]

            res = pd.DataFrame(data, columns = ['Absence de défaut de paiement', "Probabilité d'impayés"],index=[identifiant])

            st.write("## Prédiction",
                     res["Probabilité d'impayés"])

        proba = float(res["Probabilité d'impayés"].iloc[0])

        def_p = "Le client a déjà été en défaut de paiement : " + str(df_client_int['Défaut paiement'].iloc[0])
        if proba < 0.5:
            with col1:
                st.markdown("Résultat : :white_check_mark: **Faible risque d'impayés** ")
                st.write('>', def_p)
                st.write(" ")
        else:
            with col1:
                st.write("Résultat : :warning: **Risque d'impayés important, client à surveiller** ")
                st.write('>', def_p)
                st.write(' ')

        # plus proches voisins
        client_list = std.transform(df_client[interpretable_important_data])  # standardisation
        distance, voisins = nn.kneighbors(client_list)
        voisins = voisins[0]
        # on crée un dataframe avec les voisins
        voisins_table = pd.DataFrame()
        for v in range(len(voisins)):
            voisins_table[v] = df_nn.iloc[voisins[v]]
        with col3:
            st.write("## Profils de clients similaires ")
            voisins_int = pd.DataFrame(index=range(len(voisins_table.transpose())),
                                       columns=df_int.columns)
            i = 0
            for id in voisins_table.transpose()['SK_ID_CURR']:
                voisins_int.iloc[i] = df_int[df_int['Identifiant'] == id]
                i += 1
            voisins_int.set_index('Identifiant', inplace=True)
            st.write(voisins_int)

        st.write("## Graphes interactifs permettant de comparer "
                     "le client à un groupe suivant un paramètre choisi")

        with st.expander("Afficher les graphes"):
            col1_1, col2_1, col3_1 = st.columns([10, 1, 10])  # crée 3 colonnes
            with col1_1:
                param = st.selectbox(label=" Veuillez choisir le paramètre à comparer : ",
                                     options=('Genre',
                                              "Type d'entreprise",
                                              "Niveau d'éducation",
                                              "Niveau de revenus",
                                              "Statut marital"))
                if param == 'Genre':
                    cat = df_group[df_group['SK_ID_CURR'] == identifiant]['CODE_GENDER'].iloc[0]
                    if cat == 'M':
                        st.write('Le client est une femme.')
                    else:
                        st.write('Le client est un homme.')

                    bar_plot(genre, 'CODE_GENDER')

                if param == "Type d'entreprise":
                    cat = df_group[df_group['SK_ID_CURR'] == identifiant]['ORGANIZATION_TYPE'].iloc[0]
                    st.write("Type d'entreprise du client : " + cat)

                    bar_plot(organization_type, 'ORGANIZATION_TYPE')

                if param == "Niveau d'éducation":
                    cat = df_group[df_group['SK_ID_CURR'] == identifiant]['NAME_EDUCATION_TYPE'].iloc[0]
                    st.write("Niveau d'éducation du client : " + cat)

                    bar_plot(education_type, 'NAME_EDUCATION_TYPE')

                if param == "Niveau de revenus":
                    cat = df_group[df_group['SK_ID_CURR'] == identifiant]['AMT_INCOME'].iloc[0]
                    st.write("Le client a des revenus situés " + cat)

                    bar_plot(income, 'AMT_INCOME')

                if param == "Statut marital":
                    cat = df_group[df_group['SK_ID_CURR'] == identifiant]['NAME_FAMILY_STATUS'].iloc[0]
                    st.write("Statut marital du client : " + cat)

                    bar_plot(family, 'NAME_FAMILY_STATUS')

            with col3_1:
                st.write(f"Graphe radar comparant notre client aux clients du même {str.lower(param)}")
                # création du graphe radar
                radar_chart(df_client_int_SU.drop('Identifiant', axis=1), param)
                
        