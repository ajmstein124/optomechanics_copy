%% Mechanical band structure of snowflake unit cell -- diamond at 619 nm
% Adapted from Bdagger_unitcell_Mech_band_Gap.m (Si, 1562 nm).
%
% Changes from original:
%   a    : 478 nm  -> 190 nm   (same a/lambda = 0.306 at lambda=619 nm)
%   d    : 182 nm  -> 72 nm    (same d/a = 0.381)
%   w    : 99 nm   -> 39 nm    (same w/a = 0.207)
%   f_r  : 25 nm   -> 10 nm    (same f_r/a = 0.052)
%   t    : 220 nm  -> 140 nm   (diamond slab, user specified)
%   f0   : 7 GHz   -> 36 GHz   (scaled: same alpha=f*a/v, v_diamond/v_Si * a_Si/a_d)
%   sweep ranges scaled by a_diamond/a_Si = 0.396
%   Material overrides: Silicon props -> Diamond (E=1050 GPa, nu=0.07, rho=3500)
%
% Expected mechanical bandgap center: ~36 GHz

frog_folder = '';
filename = 'unit_cell_3';
model = mphload([frog_folder filename]);
save_folder = [frog_folder 'simu_data\diamond_mech\'];
mkdir(save_folder);

%% Parameters
a = 190e-9;
d_sweep = linspace(-4e-9, 4e-9, 5);
w_sweep = linspace(0e-9, 8e-9, 5);
ds = 72e-9 + d_sweep;
ws = 39e-9 + w_sweep;
t = 140e-9;

[dm, wm] = meshgrid(ds, ws);
comb = [dm(:), wm(:)];

N_freqs = 10;
f0 = 36e9;

%% Set diamond material properties (override Silicon built-in)
model.material('mat1').propertyGroup('def').set('density',       '3500[kg/m^3]');
model.material('mat1').propertyGroup('def').set('youngsmodulus', '1050e9[Pa]');
model.material('mat1').propertyGroup('def').set('poissonsratio', '0.07');

for ic = 1:size(comb, 1)
    d = comb(ic, 1);
    w = comb(ic, 2);
    model.param.set('a',      num2str(a));
    model.param.set('d',      num2str(d));
    model.param.set('w',      num2str(w));
    model.param.set('f_r',    '10e-9');
    model.param.set('t',      num2str(t));
    model.param.set('N_mode', num2str(N_freqs));
    model.param.set('f_mech', num2str(f0));

    N_ks = 5;

    kxs_GM = pi/a*linspace(0, 1,   N_ks);
    kys_GM = pi/a*linspace(0, 1/sqrt(3), N_ks);
    kxs_MK = pi/a*linspace(1, 4/3, N_ks);
    kys_MK = pi/a*linspace(1/sqrt(3), 0, N_ks);
    kxs_KG = pi/a*linspace(4/3, 0, N_ks);
    kys_KG = pi/a*linspace(0, 0,  N_ks);

    kxs = [kxs_GM, kxs_MK(2:end), kxs_KG(2:end)];
    kys = [kys_GM, kys_MK(2:end), kys_KG(2:end)];
    ks  = [kxs; kys];

    freqs = zeros(length(ks), 2*N_freqs);

    for ii = 1:length(ks)
        tic
        disp(['Computing ' num2str(ii) ' out of ' num2str(length(ks)) ...
              ', kx = ' num2str(ks(1,ii)) ', ky = ' num2str(ks(2,ii))]);
        model.param.set('kFx', num2str(ks(1,ii)));
        model.param.set('kFy', num2str(ks(2,ii)));

        % Symmetric modes
        model.component('comp1').physics('solid').feature('as1').active(false);
        model.component('comp1').physics('solid').feature('sym1').active(true);
        model.sol('sol1').runAll;
        freqs(ii, 1:end/2) = mphglobal(model, 'solid.freq', 'Dataset', 'dset1');

        % Antisymmetric modes
        model.component('comp1').physics('solid').feature('sym1').active(false);
        model.component('comp1').physics('solid').feature('as1').active(true);
        model.sol('sol1').runAll;
        freqs(ii, end/2+1:end) = mphglobal(model, 'solid.freq', 'Dataset', 'dset1');

        fname = [save_folder sprintf('diamond_Mech_bands_d_%gnm_w_%gnm_ii_%s.mat', ...
                 d*1e9, w*1e9, num2str(ii))];
        save(fname, 'freqs', 'ks', 'a', 'd', 'w', 't', 'f0', 'N_ks');
        toc
    end

    %% Plot bands
    figure(); hold on;
    for jj = 1:size(freqs, 1)
        plot(jj, 1e-9*real(freqs(jj, 1:end/2)),    'b.');
        plot(jj, 1e-9*real(freqs(jj, end/2+1:end)), 'r.');
    end
    ylabel('Frequency (GHz)')
    set(gca, 'fontsize', 12)
    xticks([1, N_ks, 2*N_ks-1, 3*N_ks-2]);
    xticklabels({'\Gamma', 'M', 'K', '\Gamma'});
    xlim([1, 3*N_ks-2])
    legend('Symmetric', 'Antisymmetric')
    title(sprintf('Diamond mech, a=190nm, d=%.0fnm, w=%.0fnm, t=140nm', d*1e9, w*1e9))
    saveas(gcf, [save_folder sprintf('diamond_Mech_band_d_%gnm_w_%gnm.jpg', d*1e9, w*1e9)]);
end
