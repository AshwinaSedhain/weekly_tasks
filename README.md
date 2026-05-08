
This project is a real-time news analytics system. In simple words, it automatically collects news from the internet, understands what the news is about, and shows everything on a live dashboard that updates itself every 30 seconds.

We are collecting news from two websites. The first one is NewsAPI, which gives us news articles from hundreds of newspapers and websites around the world through a simple API. The second one is Hacker News, which is a popular website where tech people share interesting technology articles and discuss them. We fetch the top stories from both of these sources automatically.

Once the news is collected, we send it through a tool called Kafka, which works like a conveyor belt — it takes the articles from one side and delivers them to the other side for processing. Then Apache Spark picks up those articles and cleans the text by removing unnecessary characters and spaces.

After cleaning, we run machine learning on every article. We use a technique called sentiment analysis to figure out whether the news is positive, negative, or neutral. We also extract the most important keywords from each article and group similar articles together into topic clusters. On top of that, we track which keywords are appearing more and more over time to detect trending topics.

All this data is stored in two databases. PostgreSQL stores the clean structured data like sentiment scores and keywords. MongoDB stores the raw original articles exactly as they came in.

We built a REST API using FastAPI that lets anyone query this data — you can ask for the latest news, search by keyword, get sentiment statistics, or check trending topics just by calling a URL.

The dashboard is built using Dash and Plotly. It shows a pie chart of positive vs negative vs neutral news, a bar chart of trending keywords, a chart showing how many articles came from each source, and a live table of the latest articles where positive news is highlighted in green and negative news in red.

To automate everything, we use Apache Airflow which acts like a scheduler. It runs the entire pipeline automatically every 30 minutes without anyone having to do anything manually. It also runs a cleanup job every night to remove old articles.

The whole system is packaged using Docker, which means every part of the system runs in its own isolated container. You can start everything with just one command. We also wrote Kubernetes configuration files so the system can be deployed on a cloud server and scale up automatically when traffic increases. Finally, we set up a CI/CD pipeline using GitHub Actions that automatically tests the code, builds the Docker images, and deploys everything whenever new code is pushed to GitHub.

In short, this project takes raw news from the internet, processes it intelligently, stores it, and presents it visually — all automatically, all in real time.

###########################################################################################################################################################################
Yo project ek real-time news analytics system ho. Sabda ma bhannu parda, yo system automatically internet bata news collect garcha, tyo news lai machine le bujhna milne tarika le process garcha, ani sabai kura ek live dashboard ma dekhaucha jo har 30 second ma aafai update hunchha.

Hami le data dui website bata liyeko chha. Pahilo ho NewsAPI, jaha bata duniya bhar ka saya-saya newspaper ra website ka articles API ko through milcha. Dosro ho Hacker News, jo ek popular tech community website ho jaha technology related articles share ra discuss hunchha. Yo dui source bata articles automatically fetch hunchha.

Articles collect bhaye pachhi tyo data Kafka ma pathaincha. Kafka lai conveyor belt jasto bujhna sakchha, ek side bata data liyera arko side ma deliver garcha. Tyaha bata Apache Spark le articles uthaucha, text clean garcha, ani analysis ko lagi tayar garcha.

Cleaning bhaye pachhi hami le har ek article ma machine learning chalaucha. Sentiment analysis le decide garcha ki yo news positive chha, negative chha, ki neutral chha. Keyword extraction le article ko sabai bhandaa important words nikaalcha. Topic clustering le milta-julta articles lai ek saath group garcha. Ani trend detection le track garcha ki kun keywords time sanga badhdai chhan, matlab kun topic trending chha.

Yo sabai processed data dui database ma store hunchha. PostgreSQL ma clean structured data jasto ki sentiment score ra keywords rakhchha. MongoDB ma raw original articles exactly jasari aayeko thiyo tesai rakhchha.

Data access garna hami le FastAPI use garera ek REST API banayeko chha. Yo API ko through jochai pani latest news maag-na sakcha, keyword le search garna sakcha, sentiment statistics herna sakcha, ani trending topics check garna sakcha, bas ek URL call garera.

Dashboard Dash ra Plotly use garera banayeko chha. Tyaha positive, negative ra neutral news ko pie chart dekhchha. Trending keywords ko bar chart dekhchha. Kun source bata kati articles aayo tyo dekhchha. Ani ek live news table chha jaha positive news green colour ma ra negative news red colour ma highlight hunchha.

Sabai kura automate garna Apache Airflow use gareko chha. Yo ek scheduler ho jo har 30 minute ma automatically pura pipeline chalaucha, koi le manually kehi garna pardaina. Rati ek palta purano articles delete garna pani Airflow le nai kaam garcha.

Pura system Docker ma package gareko chha, matlab har service aafno alag container ma chalcha ra ek command le sabai start hunchha. Kubernetes configuration pani banayeko chha jaba cloud ma deploy garna paryo ra traffic badhe bhane automatically scale up hunchha. GitHub Actions le CI/CD pipeline handle garcha, matlab naya code push garda automatically test hunchha, Docker image build hunchha, ani deploy hunchha.
