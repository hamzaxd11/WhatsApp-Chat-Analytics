import pandas as pd
import matplotlib.pyplot as plt
import emoji
from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator
from nltk.corpus import stopwords
import streamlit as st
stop = stopwords.words('english')
plt.style.use('bmh')
import plotly.express as px
import warnings 

warnings.filterwarnings('ignore')

@st.cache
def load_data(file_name):
	#raw_data_csv = pd.read_csv(file_name, delimiter = "\t", header = None, names = ['text'])
	data = pd.read_csv(file_name, delimiter = "\t", header = None, names = ['text'])

		# Extract datetime
	data[['datetime_str','splitted']] = data["text"].str.split(" - ", 1, expand=True)
	data[['date','time']] = data["datetime_str"].str.split(", ", 1, expand=True)

	data["date"] = pd.to_datetime(data["date"], format = "%d/%m/%Y", errors='coerce')

	data = data.dropna(subset=['date'])
	data = data.drop(columns = ['datetime_str'])

	# Extract sender and message
	data[['sender','text_message']] = data['splitted'].str.split(': ', 1, expand=True)
	data = data.dropna(subset=['text_message'])
	data = data.drop(columns = ['text','splitted'])


	data['text_message'] = data['text_message'].str.lower()
	data = data[(data['text_message']!='<media omitted>') & (data['text_message']!='this message was deleted') & (data['text_message']!='you deleted this message')]
	data['text_message'] = data['text_message'].str.split()

	data['text_message'] = data['text_message'].apply(lambda x: ' '.join(item for item in x if item not in stop and 'http' not in item and not item.startswith('@') and '@' not in item))  
	data = data[(data['text_message']!='')]

	return data



def userMessageCount(data):
	sender_count_series = data.groupby(['sender']).size().sort_values(ascending=False)

	sender_count_df = pd.DataFrame(sender_count_series)

	sender_count_df = sender_count_df.reset_index()
	sender_count_df.columns = ['sender', 'count']

	fig = plt.figure()
	plt.bar(sender_count_df['sender'], sender_count_df['count'])
	plt.xlabel("User")
	plt.ylabel("Message Count")
	plt.xticks(rotation=45, ha="right")
	plt.show()
	st.pyplot(fig)




def userWordUsage(data):

	for i in users:
		person = data[data['sender']==i]

		person = pd.DataFrame(person.text_message.str.split(expand=True).stack().value_counts())
		person['Words'] = person.index
		person.columns = ['Count', 'Words']
		person.reset_index(drop=True, inplace=True)
		person_top_ten = person.head(10).sort_values(by='Count',ascending=True)

		#word_count_by_sender_top_n = word_count[word_count['sender']==i].head(10).sort_values(by='count',ascending=True)
		fig = plt.figure()
		plt.barh(person_top_ten['Words'], person_top_ten['Count'])
		plt.xlabel("Word Count")
		plt.ylabel("Word")
		plt.title(i+'\'s'+ " Word Usage")
		st.pyplot(fig)


def timeSeries(data):
	
	#daily time series

	new_time_series = pd.DataFrame(data["date"])
	new_time_series['Message Count'] = 1
	new_time_series['date'] = pd.to_datetime(new_time_series['date'])
	new_time_series.reset_index(drop=True,inplace=True)

	df_length = len(new_time_series)

	start = new_time_series['date'][0]
	end = new_time_series['date'][df_length-1]

	new = pd.DataFrame(pd.date_range(start=start, end=end), columns = ['date'])
	new['Message Count'] = 0

	combined = pd.concat([new_time_series,new])
	combined.reset_index(inplace=True,drop=True)

	daily_time_series = pd.DataFrame(combined.groupby("date").sum())
	daily_time_series.reset_index(inplace=True)


	#monthly time series
	grouped = pd.DataFrame(combined.groupby([combined.date.dt.year, combined.date.dt.month]).count())
	grouped = pd.DataFrame(grouped.date).reset_index(drop=True)
	monthly_count = grouped['date']

	timeseries = pd.DataFrame()
	timeseries['date'] = pd.to_datetime(data['date']).dt.to_period('M').unique()
	timeseries['date'] = timeseries['date'].astype(str)
	timeseries['monthly count'] = monthly_count

	timeseries = timeseries.sort_values(by='date',ascending=True)


	fig = px.line(timeseries, x="date", y="monthly count",
                 labels={
                     "date": "Month",
                     "monthly count": "Message Count"
                 },
                title="Monthly Count",width=800, height=500)
	fig.update_xaxes(nticks=40)
	st.plotly_chart(fig)


	fig = px.line(daily_time_series, x="date", y="Message Count",
	         labels={
	             "date": "Month"},
	        title="Daily Count",width=800, height=500)
	fig.update_xaxes(nticks=40)
	st.plotly_chart(fig)



def plotActivity(data):
#activity plot

	days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

	days_dict = {0: "Monday", 1: "Tuesday", 2: "Wednesday", 3: "Thursday", 4: "Friday", 5: "Saturday",
	             6: "Sunday"}

	months = ['January', 'February', 'March', 'April', 'May', 'June', 'July',
	 'August', 'September', 'October', 'November', 'December'] 

	months_dict = {1: "January", 2: "February", 3: "March", 4: "April", 5: "May", 6: "June",
	    7: "July", 8: "August", 9: "September", 10: "October", 11: "November", 12: "December"}

	activity_data = pd.DataFrame(data["text_message"])
	activity_data['Weekday'] = data['date'].dt.weekday
	activity_data['Month'] = data['date'].dt.month

	activity_data["Message Count"] = 1

	weekday_count = activity_data[['Weekday', 'Message Count']]
	weekday_count = weekday_count.groupby("Weekday").sum()
	weekday_count.reset_index(inplace=True)
	weekday_count['Weekday'] = weekday_count['Weekday'].map(days_dict)

	month_count = activity_data[['Month', 'Message Count']]
	month_count = month_count.groupby("Month").sum()
	month_count.reset_index(inplace=True)
	month_count['Month'] = month_count['Month'].map(months_dict)

	fig = px.line_polar(weekday_count, r='Message Count', theta='Weekday', line_close=True,
	            title="Weekday Activity",width=700, height=700)
	fig.update_traces(fill='toself')
	st.plotly_chart(fig)

	fig = px.line_polar(month_count, r='Message Count', theta='Month', line_close=True,
	        	title="Monthly Activity",width=700, height=700)
	fig.update_traces(fill='toself')
	st.plotly_chart(fig)


def mostActiveDays(data):
	date_by_messages = pd.DataFrame(data['date'].value_counts())
	date_by_messages.rename(columns={'date': 'count'}, inplace = True)
	date_by_messages['date'] = date_by_messages.index
	date_by_messages['date'] = date_by_messages['date'].astype(str)
	date_by_messages.reset_index(drop=True, inplace=True)
	date_by_messages = date_by_messages.head(10)

	fig = plt.figure()
	plt.barh(date_by_messages['date'], date_by_messages['count'])
	plt.xlabel("Number of messages")
	plt.ylabel("Date")
	plt.title("Dates by number of messages")
	plt.show()
	st.pyplot(fig)



def wordCloud(data):
	text = " ".join(data['text_message'])

	wordcloud = WordCloud(max_font_size=50, max_words=50, background_color="white").generate(text)
	fig = plt.figure()
	plt.imshow(wordcloud, interpolation="bilinear")
	plt.axis("off")
	st.pyplot(fig)


def individualWordCloud(data):
	data_cloud = data[['sender', 'text_message']]

	for i in users:
		sender = data_cloud[data_cloud['sender']==i]
		sender_text = " ".join(sender['text_message'])
		wordcloud = WordCloud(max_font_size=50, max_words=50, background_color="white").generate(sender_text)
		fig = plt.figure()
		plt.imshow(wordcloud, interpolation="bilinear")
		plt.title(i+'\'s'+" Word Cloud")
		plt.axis("off")
		st.pyplot(fig)



@st.cache
def emojis(data):
	emojis = pd.DataFrame(columns=['sender','emoji'])

	for sender, message in zip(data.sender, data.text_message):
	    message_split = list(message)
	    for character in message_split:
	        if character in emoji.UNICODE_EMOJI and character != "\U0001f3fc":
	            emojis = emojis.append({'sender' : sender, 'emoji' : character}, ignore_index=True)

	return emojis



def most_used_emojis(emoji_data):
	most_used = pd.DataFrame(emoji_data.groupby(['emoji']).size().sort_values(ascending=False).head(10))

	fig = px.pie(most_used, values=most_used[0], names=most_used.index)
	fig.update_traces(textposition='outside', textinfo='percent+label')
	st.plotly_chart(fig)

	st.write(most_used)



def emojis_by_user(emoji_data):

	emoji_count = pd.DataFrame(emoji_data.groupby(['sender', 'emoji']).size().sort_values(ascending=False)).reset_index()

	emoji_count.columns = ['sender', 'emoji', 'count']

	for i in users:
		emoji_count_by_sender_top_n = emoji_count[emoji_count['sender']==i].head(5).sort_values(by='count',ascending=False).reset_index(drop=True)    
		emoji_count_by_sender_top_n = pd.DataFrame(emoji_count_by_sender_top_n)

		fig = px.pie(emoji_count_by_sender_top_n, values=emoji_count_by_sender_top_n['count'],
			names=emoji_count_by_sender_top_n['emoji'],
			title=(i+'\'s'+ " Emoji Usage"))
		fig.update_traces(textposition='outside', textinfo='percent+label')
		st.plotly_chart(fig)

		st.write(emoji_count_by_sender_top_n)



def user_by_emoji(emoji_data):
	user_by_emoji = pd.DataFrame(emoji_data.groupby(['sender']).size().sort_values(ascending=False))
	user_by_emoji.rename(columns={0: 'Emoji Count'}, inplace=True)

	fig = px.pie(user_by_emoji, values=user_by_emoji['Emoji Count'],names=user_by_emoji.index,title=("Emoji Usage"))
	fig.update_traces(textposition='outside', textinfo='percent+label')
	st.plotly_chart(fig)

	st.write(user_by_emoji)




if __name__ == '__main__':
	st.set_page_config(initial_sidebar_state =("expanded"))

	st.title("WhatsApp Chat Analytics")

	st.sidebar.markdown('[![Muhammad Hamza Adnan]\
                    (https://img.shields.io/badge/Author-@hamzaxd11-gray.svg?colorA=gray&colorB=dodgerblue&logo=github)]\
                    (https://github.com/hamzaxd11/WhatsApp-Chat-Analytics/)')

	st.markdown("Analyze your Whatsapp chats and get fun insights!")

	menu = ["Home","Message Count by User","Word Usage by Person","Plot Time Series","Chat Activity","Most Active Days","Word Cloud","Individual Word Cloud",
		"Most Used Emojis","Most used Emojis by User", "Users by Emoji Count"]
	choice = st.sidebar.selectbox("Menu",menu)

	st.sidebar.markdown('**How to export your chat txt file?**')

	st.sidebar.text('1) Open your individual or group chat.')
	st.sidebar.text('2) Tap on options > More > Export chat.')
	st.sidebar.text('3) Choose Export Without Media.')
	st.sidebar.text('4) Upload the txt file over here ->')
	st.sidebar.text('5) Analyze your chat using the Menu above!')
	st.sidebar.text('')
	st.sidebar.text('')
	st.sidebar.text('')
	st.sidebar.markdown('**The data you upload WILL NOT be saved on this site or any third party website.**.')


	file = st.file_uploader("Upload File",type=['txt'])


	if file:
		data = load_data(file)

		users = set(data['sender'])

		emoji_data = emojis(data)

		if choice == "Home":
			st.header("Welcome!")
			st.success("Upload Successful")

		elif choice == "Message Count by User":
			st.header("Message Count by User")
			userMessageCount(data)


		elif choice == "Word Usage by Person":
			st.header("Word Usage by Person")
			userWordUsage(data)



		elif choice == "Plot Time Series":
			st.header("Time Series")
			timeSeries(data)	


		elif choice == "Chat Activity":
			st.header("Chat Activity")
			plotActivity(data)	



		elif choice == "Most Active Days":
			st.header("Most Active Days")
			mostActiveDays(data)	

				

		elif choice == "Word Cloud":
			st.header("Word Cloud")
			wordCloud(data)


		elif choice == "Individual Word Cloud":
			st.header("Individual Word Cloud")
			individualWordCloud(data)


		elif choice == "Most Used Emojis":
			st.header("Most Used Emojis")
			most_used_emojis(emoji_data)


		elif choice == "Most used Emojis by User":
			st.header("Most used Emojis by User")
			emojis_by_user(emoji_data)


		elif choice == "Users by Emoji Count":
			st.header("Users by Emoji Count")
			user_by_emoji(emoji_data)


		else:
			pass
