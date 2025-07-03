start <- Sys.time()
#### LOAD NECESSARY PACKAGES ----

r = getOption("repos")
r["CRAN"] = "http://cran.us.r-project.org"
options(repos = r)

if(!require(tidyverse)){
  install.packages("tidyverse")
  library(tidyverse)
}

if(!require(jsonlite)){
  install.packages("jsonlite")
  library(jsonlite)
}

if(!require(ggplot2)){
  install.packages("ggplot2")
  library(ggplot2)
}

if(!require(ggrepel)){
  install.packages("ggrepel")
  library(ggrepel)
}


if(!require(lubridate)){
  install.packages("lubridate")
  library(lubridate)
}

if(!require(catapultR)){
  utils::install.packages("https://bitbucket.org/catapultsports/catapultr/raw/master/catapultR.zip")
  library(catapultR)
}

if(!require(stringr)){
  install.packages("stringr")
  library(stringr)
}

if(!require(httr)){
  install.packages("httr")
  library(httr)
}

options(digits = 12, encoding = "UTF-8")

library(ggplot2)
library(MASS)       # Kernel Density Estimation
library(mclust)     # Gaussian Mixture Models (GMM)
library(wavelets)   # Wavelet Transform
library(cluster)    # K-Means Clustering
library(factoextra) # Clustering Visualization
library(corrplot)   # Correlation Matrix
library(dplyr)      # Data Manipulation
library(lubridate)  # For handling date/time
library(GGally)
library(plotly)


##Rename data after importing ###

df <- Full_Uganda_Data

### clean data names to make it easier to find and search ###

df <- janitor::clean_names(df)

#### find all games rather than training ####

df <- df %>% filter(tags == "game")

### change duration into mintues ####

df <- df %>% mutate(duration_min = (duration/ 60))

### filter only for 1st and 2nd half to exclude warm up ####
df <- df |> 
  filter(split_name %in% c("1st.half", "2nd.half"))

### remove any GK data ####
df <- df %>%
  filter(position!= "GK")

### change any characters to factors ### - object columns to categoricals 

df_match <- df %>%
  mutate(across(where(is.character), as.factor)) # Convert character to factor

str(df_match)

##### convert win, loss or draw or any other info into standardised format ###

df_match <- df_match %>%
  mutate(result = case_when(
    str_detect(tolower(result), "win")  ~ "Win",
    str_detect(tolower(result), "loss") ~ "Loss",
    str_detect(tolower(result), "draw") ~ "Draw",
    TRUE                                ~ result
  ))

df_match <- df_match %>%
  mutate(competition = case_when(
    str_detect(tolower(competition), "league")  ~ "League",
    str_detect(tolower(competition), "cup") ~ "Cup",
    TRUE                                ~ competition
  ))

df_match <- df_match %>%
  mutate(venue = case_when(
    str_detect(tolower(venue), "home")  ~ "Home",
    str_detect(tolower(venue), "away") ~ "Away",
    TRUE                                ~ venue
  ))

#### find only male data ####
df_match_men <- df_match %>%
  filter(str_detect(session_title, "^MD\\d+$"))

unique(df_match_men$team)

### ensure we have standardised team names ###

team_map <- tibble::tibble(
  pattern = c(
    "vipers|vipres|viper", 
    "ura", 
    "villa", 
    "police", 
    "maroons", 
    "lugazi|lugzi", 
    "bul", 
    "mbale heroes", 
    "updf", 
    "mbarara city", 
    "kcca", 
    "wakiso", 
    "kitara", 
    "solitilo|soltilo|soliyilo", 
    "nec",
    "express"
  ),
  clean_name = c(
    "Vipers SC", "URA FC", "Villa", "Police FC", "Maroons FC", "Lugazi FC",
    "Bul FC", "Mbale Heroes FC", "UPDF", "Mbarara City FC", "KCCA FC",
    "Wakiso Giants FC", "Kitara FC", "Solitilo FC", "NEC FC", "Express FC" #Soltilo Bright Stars FC
  )
)

df_match_men <- df_match_men %>%
  mutate(team = str_to_lower(str_trim(team))) %>%
  rowwise() %>%
  mutate(team = {
    matched <- team_map$clean_name[str_detect(team, team_map$pattern)]
    if (length(matched) > 0) matched[1] else str_to_title(team)
  }) %>%
  ungroup()

#### remove womens data which was incorreclty labelled with MD ####
df_match_men <- df_match_men %>%
  filter(
    !str_detect(tolower(team), "kampala queens fc|kampala queens|amus college")
  )


#### group first and second half data into full game data #####

df_combined <- df_match_men %>%
  group_by(team, session_title,player_name,position) %>%
  summarise(
    across(
      .cols = c(distance_km, sprint_distance_m, duration_min,
                distance_in_speed_zone_1_km:distance_in_speed_zone_5_km),
      .fns = ~sum(.x, na.rm = TRUE)
    ),
    top_speed = max(top_speed_km_h, na.rm = TRUE),
    distance_per_min = sum(distance_km * 1000, na.rm = TRUE) / sum(duration_min, na.rm = TRUE),
    .groups = "drop"
  )
df_combined7 <- df_combined

#### filter out players below 60mins or 2 km for outliers ####

df_combined7 <- df_combined7 |> 
  filter(duration_min >= 60,distance_km >=2)

### check data 
summary(df_combined$duration_min)

boxplot(df_combined7$duration_min, main = "Boxplot of Column", ylab = "Values")

# Calculate IQR bounds for distance_km ###
Q1_dist <- quantile(df_combined7$distance_km, 0.25, na.rm = TRUE)
Q3_dist <- quantile(df_combined7$distance_km, 0.75, na.rm = TRUE)
IQR_dist <- Q3_dist - Q1_dist

lower_dist <- Q1_dist - 1.5 * IQR_dist
upper_dist <- Q3_dist + 1.5 * IQR_dist

# Calculate IQR bounds for duration_min ### 
Q1_dur <- quantile(df_combined7$duration_min, 0.25, na.rm = TRUE)
Q3_dur <- quantile(df_combined7$duration_min, 0.75, na.rm = TRUE)
IQR_dur <- Q3_dur - Q1_dur

lower_dur <- Q1_dur - 1.5 * IQR_dur
upper_dur <- Q3_dur + 1.5 * IQR_dur

# Filter data: keep only rows within bounds for BOTH columns ###
df_no_outliers <- df_combined7 %>%
  filter(
    distance_km >= lower_dist & distance_km <= upper_dist,
    duration_min >= lower_dur & duration_min <= upper_dur
  )

#### change output based on what we want to look at. Can look at player, match day, position or team. Group accordingly ###


df_summary_position_MD <- df_combined7 %>%
  group_by(position,session_title) %>%
  summarise(
    avg_distance_km = mean(distance_km, na.rm = TRUE),
    avg_sprint_m = mean(sprint_distance_m, na.rm = TRUE),
    max_top_speed_kmh = max(top_speed, na.rm = TRUE),  
    avg_distance_per_min = mean(distance_per_min, na.rm = TRUE),
    avg_SZ1_km = mean(distance_in_speed_zone_1_km, na.rm = TRUE),
    avg_SZ2_km = mean(distance_in_speed_zone_2_km, na.rm = TRUE),
    avg_SZ3_km = mean(distance_in_speed_zone_3_km, na.rm = TRUE),
    avg_SZ4_km = mean(distance_in_speed_zone_4_km, na.rm = TRUE),
    avg_SZ5_km = mean(distance_in_speed_zone_5_km, na.rm = TRUE),
    .groups = "drop"
  )


#### create a CSV of the data to use in presentaitons ####
 write.csv(df_summary, "match_summary.csv", row.names = FALSE)
