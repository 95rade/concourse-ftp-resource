from conftest import cmd, make_files


def test_check_one_file(ftp_root, ftp_server):
    """Test if one uploaded file returns one version."""

    make_files(ftp_root, ['filename-0.0.0.tgz'])

    source = {
        "uri": ftp_server,
        "regex": "(?P<file>filename-(?P<version>.*).tgz)"
    }

    result = cmd('check', source)

    assert result == [{"version": "0.0.0"}]


def test_semver(ftp_root, ftp_server):
    """Test if semver versions don't break."""

    make_files(ftp_root, ['filename-1.0.0-rc.1.tgz'])

    source = {
        "uri": ftp_server,
        "regex": "(?P<file>filename-(?P<version>.*).tgz)"
    }

    result = cmd('check', source)

    assert result == [{"version": "1.0.0-rc.1"}]


def test_check_multiple_files(ftp_root, ftp_server):
    """Test if multiple uploaded file return more versions."""

    make_files(ftp_root, ['filename-0.0.0.tgz', 'filename-0.0.1.tgz'])

    source = {
        "uri": ftp_server,
        "regex": "(?P<file>filename-(?P<version>.*).tgz)"
    }

    result = cmd('check', source)

    assert result == [{"version": "0.0.1"}], 'should only return most recent version'


def test_check_passing_version(ftp_root, ftp_server):
    """Test when a version is passed only new versions are returned."""

    make_files(ftp_root, [
        'filename-0.0.0.tgz', 'filename-0.0.1.tgz', 'filename-0.0.2.tgz', 'filename-0.0.3.tgz'
    ])

    source = {
        "uri": ftp_server,
        "regex": "(?P<file>filename-(?P<version>.*).tgz)"
    }

    result = cmd('check', source, version={"version": "0.0.1"})

    assert {"version": "0.0.2"} in result, 'new version should be in result'
    assert {"version": "0.0.3"} in result, 'new version should be in result'
    assert {"version": "0.0.0"} not in result, 'older version should not be in result'
    assert {"version": "0.0.1"} not in result, 'current version should not be in result'


def test_check_no_new_version(ftp_root, ftp_server):
    """When passing a version an no newer files return nothing."""

    make_files(ftp_root, ['filename-0.0.0.tgz', 'filename-0.0.1.tgz'])

    source = {
        "uri": ftp_server,
        "regex": "(?P<file>filename-(?P<version>.*).tgz)"
    }

    result = cmd('check', source, version={"version": "0.0.1"})

    assert result == []
