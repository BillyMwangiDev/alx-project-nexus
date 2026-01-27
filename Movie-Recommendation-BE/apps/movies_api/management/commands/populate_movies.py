from django.core.management.base import BaseCommand
from apps.movies_api.models import MovieMetadata
from datetime import date


class Command(BaseCommand):
    help = 'Populate database with sample movie data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Populating database with sample movies...')
        
        movies_data = [
            {
                'tmdb_id': 550,
                'title': 'Fight Club',
                'overview': 'A ticking-time-bomb insomniac and a slippery soap salesman channel primal male aggression into a shocking new form of therapy.',
                'release_date': date(1999, 10, 15),
                'poster_path': '/pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg',
                'backdrop_path': '/fCayJrkfRaCRCTh8GqN30f8oyQF.jpg',
                'vote_average': 8.4,
                'vote_count': 28000,
                'popularity': 95.3,
                'genres': ['Drama', 'Thriller', 'Comedy'],
                'runtime': 139
            },
            {
                'tmdb_id': 278,
                'title': 'The Shawshank Redemption',
                'overview': 'Framed in the 1940s for the double murder of his wife and her lover, upstanding banker Andy Dufresne begins a new life at the Shawshank prison.',
                'release_date': date(1994, 9, 23),
                'poster_path': '/q6y0Go1tsGEsmtFryDOJo3dEmqu.jpg',
                'backdrop_path': '/kXfqcdQKsToO0OUXHcrrNCHDBzO.jpg',
                'vote_average': 8.7,
                'vote_count': 25000,
                'popularity': 92.5,
                'genres': ['Drama', 'Crime'],
                'runtime': 142
            },
            {
                'tmdb_id': 238,
                'title': 'The Godfather',
                'overview': 'Spanning the years 1945 to 1955, a chronicle of the fictional Italian-American Corleone crime family.',
                'release_date': date(1972, 3, 14),
                'poster_path': '/3bhkrj58Vtu7enYsRolD1fZdja1.jpg',
                'backdrop_path': '/tmU7GeKVybMWFButWEGl2M4GeiP.jpg',
                'vote_average': 8.7,
                'vote_count': 18000,
                'popularity': 89.7,
                'genres': ['Drama', 'Crime'],
                'runtime': 175
            },
            {
                'tmdb_id': 424,
                'title': 'Schindler\'s List',
                'overview': 'The true story of how businessman Oskar Schindler saved over a thousand Jewish lives during the Holocaust.',
                'release_date': date(1993, 12, 15),
                'poster_path': '/sF1U4EUQS8YHUYjNl3pMGNIQyr0.jpg',
                'backdrop_path': '/loRmRzQXZeqG78TqZuyvSlEQfZb.jpg',
                'vote_average': 8.6,
                'vote_count': 14000,
                'popularity': 85.2,
                'genres': ['Drama', 'History', 'War'],
                'runtime': 195
            },
            {
                'tmdb_id': 680,
                'title': 'Pulp Fiction',
                'overview': 'A burger-loving hit man, his philosophical partner, and a drug-addled gangster\'s moll are caught up in a world of violence and redemption.',
                'release_date': date(1994, 10, 14),
                'poster_path': '/d5iIlFn5s0ImszYzBPb8JPIfbXD.jpg',
                'backdrop_path': '/4cDFJr4HnXN5AdPw4AKrmLlMWdO.jpg',
                'vote_average': 8.5,
                'vote_count': 26000,
                'popularity': 94.8,
                'genres': ['Thriller', 'Crime'],
                'runtime': 154
            },
            {
                'tmdb_id': 13,
                'title': 'Forrest Gump',
                'overview': 'A simple man witnesses and influences many defining historical events in the 20th century United States.',
                'release_date': date(1994, 7, 6),
                'poster_path': '/arw2vcBveWOVZr6pxd9XTd1TdQa.jpg',
                'backdrop_path': '/7c9UVPPiTPltouxRVY6N9uUaHRN.jpg',
                'vote_average': 8.5,
                'vote_count': 24000,
                'popularity': 91.3,
                'genres': ['Comedy', 'Drama', 'Romance'],
                'runtime': 142
            },
            {
                'tmdb_id': 155,
                'title': 'The Dark Knight',
                'overview': 'Batman raises the stakes in his war on crime with the help of Lt. Jim Gordon and District Attorney Harvey Dent.',
                'release_date': date(2008, 7, 18),
                'poster_path': '/qJ2tW6WMUDux911r6m7haRef0WH.jpg',
                'backdrop_path': '/hkBaDkMWbLaf8B1lsWsKX7Ew3Xq.jpg',
                'vote_average': 9.0,
                'vote_count': 30000,
                'popularity': 98.5,
                'genres': ['Drama', 'Action', 'Crime', 'Thriller'],
                'runtime': 152
            },
            {
                'tmdb_id': 129,
                'title': 'Spirited Away',
                'overview': 'A young girl becomes trapped in a strange new world of spirits during her family\'s move to the suburbs.',
                'release_date': date(2001, 7, 20),
                'poster_path': '/39wmItIWsg5sZMyRUHLkWBcuVCM.jpg',
                'backdrop_path': '/Ab8mkHmkYADjU7wQiOkia9BzGvS.jpg',
                'vote_average': 8.5,
                'vote_count': 15000,
                'popularity': 87.9,
                'genres': ['Animation', 'Family', 'Fantasy'],
                'runtime': 125
            },
            {
                'tmdb_id': 497,
                'title': 'The Green Mile',
                'overview': 'A tale set on death row in a Southern prison, where gentle giant John Coffey possesses mysterious powers.',
                'release_date': date(1999, 12, 10),
                'poster_path': '/velWPhVMQeQKcxggNEU8YmIo52R.jpg',
                'backdrop_path': '/l6hQWH9eDksNJNiXWYRkWqikOdu.jpg',
                'vote_average': 8.5,
                'vote_count': 16000,
                'popularity': 88.4,
                'genres': ['Fantasy', 'Drama', 'Crime'],
                'runtime': 189
            },
            {
                'tmdb_id': 19404,
                'title': 'Dilwale Dulhania Le Jayenge',
                'overview': 'Raj and Simran meet on a trip across Europe and fall in love, but Simran is promised to another.',
                'release_date': date(1995, 10, 20),
                'poster_path': '/2CAL2433ZeIihfX1Hb2139CX0pW.jpg',
                'backdrop_path': '/90ez6ArvpO8bvpyIngBuwXOqJm5.jpg',
                'vote_average': 8.7,
                'vote_count': 4000,
                'popularity': 79.2,
                'genres': ['Comedy', 'Drama', 'Romance'],
                'runtime': 181
            },
            {
                'tmdb_id': 857,
                'title': 'Saving Private Ryan',
                'overview': 'Following the Normandy Landings, a group of U.S. soldiers go behind enemy lines to retrieve a paratrooper.',
                'release_date': date(1998, 7, 24),
                'poster_path': '/uqx37WkN3SjgGFMz8bXTgWbZB3A.jpg',
                'backdrop_path': '/hdYKqJ2Z8yCUkC1dGvl5LZULEb6.jpg',
                'vote_average': 8.2,
                'vote_count': 13000,
                'popularity': 86.5,
                'genres': ['Drama', 'History', 'War'],
                'runtime': 169
            },
            {
                'tmdb_id': 244786,
                'title': 'Whiplash',
                'overview': 'A promising young drummer enrolls at a cut-throat music conservatory where his dreams hang in the balance.',
                'release_date': date(2014, 10, 10),
                'poster_path': '/7fn624j5lj3xTme2SgiLCeuedmO.jpg',
                'backdrop_path': '/6bbZ6XyvgfjhQwbplnUh1LSj1ky.jpg',
                'vote_average': 8.3,
                'vote_count': 13000,
                'popularity': 90.1,
                'genres': ['Drama', 'Music'],
                'runtime': 107
            },
            {
                'tmdb_id': 603,
                'title': 'The Matrix',
                'overview': 'A computer hacker learns about the true nature of reality and his role in the war against its controllers.',
                'release_date': date(1999, 3, 31),
                'poster_path': '/f89U3ADr1oiB1s9GkdPOEpXUk5H.jpg',
                'backdrop_path': '/icmmSD4vTTDKOq2vvdulafOGw93.jpg',
                'vote_average': 8.2,
                'vote_count': 23000,
                'popularity': 93.7,
                'genres': ['Action', 'Science Fiction'],
                'runtime': 136
            },
            {
                'tmdb_id': 122,
                'title': 'The Lord of the Rings: The Return of the King',
                'overview': 'Gandalf and Aragorn lead the World of Men against Sauron\'s army to draw his gaze from Frodo and Sam.',
                'release_date': date(2003, 12, 17),
                'poster_path': '/rCzpDGLbOoPwLjy3OAm5NUPOTrC.jpg',
                'backdrop_path': '/2u7zbn8EudG6kLlBzUYqP8RyFU4.jpg',
                'vote_average': 8.5,
                'vote_count': 22000,
                'popularity': 94.2,
                'genres': ['Adventure', 'Fantasy', 'Action'],
                'runtime': 201
            },
            {
                'tmdb_id': 27205,
                'title': 'Inception',
                'overview': 'A thief who steals corporate secrets through dream-sharing technology is given the inverse task of planting an idea.',
                'release_date': date(2010, 7, 16),
                'poster_path': '/9gk7adHYeDvHkCSEqAvQNLV5Uge.jpg',
                'backdrop_path': '/s3TBrRGB1iav7gFOCNx3H31MoES.jpg',
                'vote_average': 8.4,
                'vote_count': 32000,
                'popularity': 97.8,
                'genres': ['Action', 'Science Fiction', 'Adventure'],
                'runtime': 148
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        for movie_data in movies_data:
            movie, created = MovieMetadata.objects.update_or_create(
                tmdb_id=movie_data['tmdb_id'],
                defaults=movie_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'✓ Created: {movie.title}'))
            else:
                updated_count += 1
                self.stdout.write(self.style.WARNING(f'↻ Updated: {movie.title}'))
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Done! Created: {created_count}, Updated: {updated_count}'))