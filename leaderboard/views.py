"""
Project OCELoT: Open, Competitive Evaluation Leaderboard of Translations
"""
from collections import OrderedDict

from django.contrib import messages
from django.shortcuts import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from leaderboard.forms import SigninForm
from leaderboard.forms import SubmissionForm
from leaderboard.forms import TeamForm
from leaderboard.models import Submission
from leaderboard.models import Team
from leaderboard.models import TestSet


MAX_SUBMISSION_DISPLAY_COUNT = 10
MAX_SUBMISSION_LIMIT = 7


def _get_team_data(request):
    """Returns team name for session token."""
    ocelot_team_name = None
    ocelot_team_email = None
    ocelot_team_token = request.session.get('ocelot_team_token')
    if ocelot_team_token:
        the_team = Team.objects.get(  # pylint: disable=no-member
            token=ocelot_team_token
        )
        ocelot_team_name = the_team.name
        ocelot_team_email = the_team.email
    return (ocelot_team_name, ocelot_team_email, ocelot_team_token)


def frontpage(request):
    """Renders OCELoT frontpage."""

    test_sets = TestSet.objects.filter(  # pylint: disable=no-member
        is_active=True
    )

    data = OrderedDict()
    for test_set in test_sets:
        submissions = (
            Submission.objects.filter(  # pylint: disable=no-member
                test_set=test_set,
                score__gte=0,  # Ignore invalid submissions
            )
            .order_by('-score',)
            .values_list(
                'id',
                'score',
                'score_chrf',
                'date_created',
                'submitted_by__token',
            )[:MAX_SUBMISSION_DISPLAY_COUNT]
        )
        for submission in submissions:
            key = str(test_set)
            if not key in data.keys():
                data[key] = []
            data[key].append(submission)

    (
        ocelot_team_name,
        ocelot_team_email,
        ocelot_team_token,
    ) = _get_team_data(request)

    context = {
        'data': data.items(),
        'deadline': '6/30/2020 12:00:00 UTC',
        'MAX_SUBMISSION_DISPLAY_COUNT': MAX_SUBMISSION_DISPLAY_COUNT,
        'ocelot_team_name': ocelot_team_name,
        'ocelot_team_email': ocelot_team_email,
        'ocelot_team_token': ocelot_team_token,
    }
    return render(request, 'leaderboard/frontpage.html', context=context)


def signin(request):
    """Renders OCELoT team sign-in page."""

    # Already signed in?
    if request.session.get('ocelot_team_token'):
        _msg = 'You are already signed in.'
        messages.info(request, _msg)
        return HttpResponseRedirect(reverse('frontpage-view'))

    if request.method == 'POST':
        form = SigninForm(request.POST)

        if form.is_valid():
            the_team = Team.objects.filter(  # pylint: disable=no-member
                name=form.cleaned_data['name'],
                email=form.cleaned_data['email'],
                token=form.cleaned_data['token'],
            )
            if the_team.exists():
                request.session['ocelot_team_token'] = form.cleaned_data[
                    'token'
                ]

            _msg = 'You have successfully signed in.'
            messages.success(request, _msg)
            return HttpResponseRedirect(reverse('frontpage-view'))

    else:
        form = SigninForm()

    context = {'form': form}
    return render(request, 'leaderboard/sign-in.html', context=context)


def signout(request):
    """Clears current OCELoT session."""
    del request.session['ocelot_team_token']
    messages.success(request, 'You have successfully signed out.')
    return HttpResponseRedirect(reverse('frontpage-view'))


def signup(request):
    """Renders OCELoT team signup page."""

    if request.session.get('ocelot_team_token'):
        messages.info(request, 'You are already signed up.')
        return HttpResponseRedirect(reverse('frontpage-view'))

    if request.method == 'POST':
        form = TeamForm(request.POST)

        if form.is_valid():
            new_team = form.save()
            request.session['ocelot_team_token'] = new_team.token
            messages.success(request, 'You have successfully signed up.')
            return HttpResponseRedirect(reverse('welcome-view'))

    else:
        form = TeamForm()

    context = {'form': form}
    return render(request, 'leaderboard/signup.html', context=context)


def submit(request):
    """Renders OCELoT submission page."""

    (
        ocelot_team_name,
        ocelot_team_email,
        ocelot_team_token,
    ) = _get_team_data(request)

    if not ocelot_team_token:
        _msg = 'You need to be signed in to access this page.'
        messages.warning(request, _msg)
        return HttpResponseRedirect('/')

    if request.method == 'POST':
        form = SubmissionForm(request.POST, request.FILES)

        if form.is_valid():
            current_team = Team.objects.get(  # pylint: disable=no-member
                token=ocelot_team_token
            )
            print(current_team)

            submissions_for_team_and_test_set = Submission.objects.filter(  # pylint: disable=no-member
                submitted_by=current_team,
                test_set=form.cleaned_data['test_set'],
                score__gte=0,  # Ignore invalid submissions for limit check
            ).count()
            print(submissions_for_team_and_test_set)

            if submissions_for_team_and_test_set >= MAX_SUBMISSION_LIMIT:
                _msg = 'You have reached the submission limit for {0}.'.format(
                    form.cleaned_data['test_set']
                )
                messages.warning(request, _msg)
                return HttpResponseRedirect('/')

            new_submission = form.save(commit=False)
            new_submission.name = form.cleaned_data['sgml_file'].name
            new_submission.submitted_by = current_team
            new_submission.save()

            _msg = 'You have successfully submitted {0}'.format(
                new_submission.sgml_file.name
            )
            messages.success(request, _msg)
            return HttpResponseRedirect(reverse('teampage-view'))

    else:
        form = SubmissionForm()

    context = {
        'form': form,
        'ocelot_team_name': ocelot_team_name,
        'ocelot_team_email': ocelot_team_email,
        'ocelot_team_token': ocelot_team_token,
    }
    return render(request, 'leaderboard/submission.html', context=context)


def teampage(request):
    """Renders OCELoT team page."""

    (
        ocelot_team_name,
        ocelot_team_email,
        ocelot_team_token,
    ) = _get_team_data(request)

    if not ocelot_team_token:
        _msg = 'You need to be signed in to access this page.'
        messages.warning(request, _msg)
        return HttpResponseRedirect('/')

    data = OrderedDict()
    submissions = Submission.objects.filter(  # pylint: disable=no-member
        test_set__is_active=True,
        score__gte=0,  # Ignore invalid submissions
        submitted_by__token=ocelot_team_token,
    )
    ordering = (
        'test_set__name',
        'test_set__source_language__code',
        'test_set__target_language__code',
        '-score',
    )
    for submission in submissions.order_by(*ordering):
        key = str(submission.test_set)
        if not key in data.keys():
            data[key] = []
        data[key].append(submission)

    context = {
        'data': data.items(),
        'MAX_SUBMISSION_LIMIT': MAX_SUBMISSION_LIMIT,
        'ocelot_team_name': ocelot_team_name,
        'ocelot_team_email': ocelot_team_email,
        'ocelot_team_token': ocelot_team_token,
    }
    return render(request, 'leaderboard/teampage.html', context=context)


def updates(request):
    """Renders OCELoT updates page."""

    (
        ocelot_team_name,
        ocelot_team_email,
        ocelot_team_token,
    ) = _get_team_data(request)

    context = {
        'MAX_SUBMISSION_LIMIT': MAX_SUBMISSION_LIMIT,
        'ocelot_team_name': ocelot_team_name,
        'ocelot_team_email': ocelot_team_email,
        'ocelot_team_token': ocelot_team_token,
    }
    return render(request, 'leaderboard/updates.html', context=context)


def welcome(request):
    """Renders OCELoT welcome (registration confirmation) page."""

    (
        ocelot_team_name,
        ocelot_team_email,
        ocelot_team_token,
    ) = _get_team_data(request)

    if not ocelot_team_token:
        _msg = 'You need to be signed in to access this page.'
        messages.warning(request, _msg)
        return HttpResponseRedirect('/')

    context = {
        'ocelot_team_name': ocelot_team_name,
        'ocelot_team_email': ocelot_team_email,
        'ocelot_team_token': ocelot_team_token,
    }
    return render(request, 'leaderboard/welcome.html', context=context)
