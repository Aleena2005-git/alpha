from django.shortcuts import render

# Create your views here.
import hashlib
import secrets
from .models import Voter
from django.shortcuts import render, redirect
from .blockchain import Blockchain
from .models import Election
from django.shortcuts import render, redirect
from .models import Voter, Election
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import logout
from .models import Voter
from django.shortcuts import render, redirect
from .models import Election, Post
from .models import Post, Candidate
from .models import Block

blockchain = Blockchain()


def generate_wallet():
    private_key = secrets.token_hex(32)
    wallet_hash = hashlib.sha256(private_key.encode()).hexdigest()
    wallet_address = "0x" + wallet_hash[:40]
    return wallet_address

def register_voter(request):
    request.session['show_navbar'] = True

    if request.method == "POST":
        wallet = generate_wallet()

        # Save voter in database
        Voter.objects.create(wallet_address=wallet)

        # Show the register page with registered flag so template shows Login
        return render(request, "register.html", {
            "registered": True,
            "wallet": wallet
        })

    # Ensure template gets a registered flag on GET (False) so the register
    # button is shown when appropriate.
    return render(request, "register.html", {"registered": False})




@staff_member_required(login_url='admin:login')
def admin_dashboard(request):
    request.session['show_navbar'] = True

    voters = Voter.objects.all()
    elections = Election.objects.all()
    return render(request, "admin_dashboard.html", {
        "voters": voters,
        "elections": elections
    })


@staff_member_required(login_url='admin:login')
def admin_logout(request):
    logout(request)
    request.session.pop('show_navbar', None)
    return redirect('home')

@staff_member_required(login_url='admin:login')
def approve_voter(request, voter_id):
    voter = Voter.objects.get(id=voter_id)
    voter.approved = True
    voter.save()
    return redirect('admin_dashboard')


@staff_member_required(login_url='admin:login')
def toggle_election(request, election_id):
    election = Election.objects.get(id=election_id)
    election.is_active = not election.is_active
    election.save()
    return redirect('admin_dashboard')

def home(request):
    return render(request, "home.html")



@staff_member_required(login_url='admin:login')
def create_election(request):
    if request.method == "POST":
        print("FORM SUBMITTED")
        name = request.POST.get("election_name")
        print("Election Name:", name)

        Election.objects.create(name=name)
        print("Saved to DB")

        return redirect('admin_dashboard')

    return render(request, 'create_election.html')


@staff_member_required(login_url='admin:login')
def create_post(request):
    elections = Election.objects.all()

    if request.method == "POST":
        post_name = request.POST.get("post_name")
        election_id = request.POST.get("election_id")

        election = Election.objects.get(id=election_id)

        Post.objects.create(
            name=post_name,
            election=election
        )

        return redirect('admin_dashboard')

    return render(request, 'create_post.html', {
        'elections': elections
    }) 





@staff_member_required(login_url='admin:login')
def create_candidate(request):
    posts = Post.objects.all()

    if request.method == "POST":
        candidate_name = request.POST.get("candidate_name")
        post_id = request.POST.get("post_id")

        post = Post.objects.get(id=post_id)

        # New fields: semester and department
        semester = request.POST.get("semester")
        department = request.POST.get("department")

        Candidate.objects.create(
            name=candidate_name,
            post=post,
            semester=(int(semester) if semester else None),
            department=(department or "")
        )

        return redirect('admin_dashboard')

    return render(request, 'create_candidate.html', {'posts': posts})  





from django.shortcuts import render, redirect
from .models import Voter, Election, Post, Candidate
from django.db import models

def voter_login(request):
    request.session['show_navbar'] = True

    if request.method == "POST":
        wallet = request.POST.get("wallet")

        try:
            voter = Voter.objects.get(wallet_address=wallet)

            if voter.approved:
                request.session['wallet'] = wallet
                return redirect('voter_dashboard')
            else:
                return render(request, 'voter_login.html', {
                    'error': "Your account is not approved by admin."
                })

        except Voter.DoesNotExist:
            return render(request, 'voter_login.html', {
                'error': "Wallet address not found."
            })

    return render(request, 'voter_login.html')


def voter_logout(request):
    # Remove the wallet from session to log the voter out
    request.session.pop('wallet', None)
    return redirect('home')




from .models import Election

def voter_dashboard(request):
    if not request.session.get("wallet"):
        return redirect("voter_login")

    voter = Voter.objects.get(wallet_address=request.session["wallet"])
    active_elections = Election.objects.filter(is_active=True).order_by("name")

    return render(request, "voter_dashboard.html", {
        "voter": voter,
        "active_elections": active_elections,
    })






def cast_vote(request, candidate_id):
    if 'wallet' not in request.session:
        return redirect('voter_login')

    wallet = request.session['wallet']

    candidate = Candidate.objects.get(id=candidate_id)

    # Ensure election is active
    if not candidate.post.election.is_active:
        return render(request, 'vote_error.html', {
            'error': "This election is not active."
        })

    # Prevent double voting for the same post (allow voting across different posts)
    if Block.objects.filter(voter_wallet=wallet, candidate__post=candidate.post).exists():
        return render(request, 'vote_error.html', {
            'error': "You have already voted for this post!"
        })

    # Get last block
    last_block = Block.objects.order_by('-id').first()
    previous_hash = last_block.hash if last_block else "0"

    # Simulate gas used for this transaction (simple deterministic pseudo-gas)
    import secrets
    gas_sim = 21000 + (secrets.randbelow(4000))

    block = Block(
        voter_wallet=wallet,
        candidate=candidate,
        previous_hash=previous_hash,
        gas_used=gas_sim
    )

    block.save()
    # After saving, check if voter has now voted for all posts in this election
    election = candidate.post.election
    posts = Post.objects.filter(election=election)

    all_voted = True
    for post in posts:
        if not Block.objects.filter(voter_wallet=wallet, candidate__post=post).exists():
            all_voted = False
            break

    return render(request, 'vote_success.html', {
        'candidate': candidate,
        'election': election,
        'all_voted': all_voted,
    })



from django.db.models import Count
from .models import Block

def results_view(request):
    elections = Election.objects.order_by('-is_active', 'name')
    selected_election = None
    selected_election_id = request.GET.get('election')

    if selected_election_id:
        selected_election = Election.objects.filter(id=selected_election_id).first()

    if not selected_election:
        selected_election = elections.filter(is_active=True).first() or elections.first()

    vote_rows = Block.objects.all()
    if selected_election:
        vote_rows = vote_rows.filter(candidate__post__election=selected_election)

    # Count votes per candidate
    results = vote_rows.values(
        'candidate__name',
        'candidate__post__name',
        'candidate__department',
        'candidate__semester',
    ).annotate(total_votes=Count('id')).order_by('candidate__post__name', '-total_votes', 'candidate__name')

    # Add rank per post (same votes share same rank)
    ranked_results = []
    current_post = None
    last_votes = None
    current_rank = 0

    for row in results:
        post_name = row['candidate__post__name']
        votes = row['total_votes']

        if post_name != current_post:
            current_post = post_name
            last_votes = None
            current_rank = 0

        if votes != last_votes:
            current_rank += 1
            last_votes = votes

        row['rank'] = current_rank
        ranked_results.append(row)

    total_votes = sum(row['total_votes'] for row in ranked_results)
    candidate_count = len(ranked_results)
    distribution = sorted(ranked_results, key=lambda row: (-row['total_votes'], row['candidate__name']))
    leading_candidate = distribution[0] if distribution else None

    for row in ranked_results:
        row['percentage'] = round((row['total_votes'] / total_votes) * 100) if total_votes else 0
    for row in distribution:
        row['percentage'] = round((row['total_votes'] / total_votes) * 100) if total_votes else 0

    return render(request, 'results.html', {
        'results': ranked_results,
        'distribution': distribution,
        'total_votes': total_votes,
        'candidate_count': candidate_count,
        'leading_candidate': leading_candidate,
        'elections': elections,
        'selected_election': selected_election,
    })    


@staff_member_required(login_url='admin:login')
def blockchain_view(request):
    request.session['show_navbar'] = True
    active_elections = Election.objects.filter(is_active=True).count()
    transactions = Block.objects.order_by('-id')

    total_transactions = transactions.count()
    vote_transactions = transactions.count()
    latest_block = transactions.first()
    total_gas = transactions.aggregate(total=models.Sum('gas_used'))['total'] or 0

    return render(request, 'blockchain.html', {
        'active_elections': active_elections,
        'transactions': transactions,
        'total_gas': total_gas,
        'total_transactions': total_transactions,
        'vote_transactions': vote_transactions,
        'latest_block_number': latest_block.id if latest_block else 0,
    })


from .models import Post

def view_election(request, election_id):
    election = Election.objects.get(id=election_id)
    posts = Post.objects.filter(election=election)

    # all candidates for these posts (template may also use post.candidate_set)
    candidates = Candidate.objects.filter(post__in=posts)

    wallet = request.session.get('wallet')

    # For each post determine whether the current voter already voted for that post
    voted_posts = {}
    if wallet:
        for post in posts:
            voted_posts[post.id] = Block.objects.filter(voter_wallet=wallet, candidate__post=post).exists()
    else:
        for post in posts:
            voted_posts[post.id] = False

    # list of post ids the voter has voted for (template-friendly)
    voted_post_ids = [pid for pid, val in voted_posts.items() if val]

    # Also compute set of candidate ids the voter has voted for
    voted_candidate_ids = set(Block.objects.filter(voter_wallet=wallet).values_list('candidate_id', flat=True)) if wallet else set()

    return render(request, "view_election.html", {
        "election": election,
        "posts": posts,
        "candidates": candidates,
        "voted_posts": voted_posts,
        "voted_post_ids": voted_post_ids,
        "wallet": wallet,
        "voted_candidate_ids": voted_candidate_ids,
    })    
